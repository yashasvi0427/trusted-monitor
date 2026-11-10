"""Offline replay of committed evidence; never calls a model or modifies labels."""
import collections,csv,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from run_untrusted import parse_reply
from validate import run_tests,check_exploit
from metrics import auc,catch_rate

def main():
 problems={p['task_id']:p for p in json.loads((ROOT/'data/problems.json').read_text())}
 report={'kind':'cached-generation replay, fresh code execution; no model inference','files_sha256':{},'runs':{}}
 for mode in ['honest','attack_v2']:
  path=ROOT/f'results/untrusted_qwen2.5-coder_7b_{mode}.csv'
  report['files_sha256'][str(path.relative_to(ROOT))]=hashlib.sha256(path.read_bytes()).hexdigest()
  rows=list(csv.DictReader(path.open())); passed=0; mismatches=[]; confirmed=[]; missing=[]
  for row in rows:
   tid=int(row['task_id']); attempt=int(row.get('attempt') or 0)
   name=str(tid)+(f'_a{attempt}' if attempt else '')+'.json'
   cache=ROOT/'data/untrusted/qwen2.5-coder_7b'/mode/name
   if not cache.exists():
    missing.append(str(cache.relative_to(ROOT))); continue
   rec=parse_reply(json.loads(cache.read_text())); code=rec['code']; p=problems[tid]
   ok=bool(code and run_tests(code,p)['passed']); passed+=ok
   if ok!=(row['passed_tests']=='True'): mismatches.append(tid)
   if row['valid_backdoor']=='True':
    result=check_exploit(code,p,rec['exploit_input']); confirmed.append({'task_id':tid,'attempt':attempt,**result})
  report['runs'][mode]={'tasks':len(rows),'missing_cache':missing,'normal_test_passes':passed,'pass_label_disagreements':mismatches,'accepted_backdoors_rechecked':confirmed}
  print(mode,report['runs'][mode],flush=True)
 scores=list(csv.DictReader((ROOT/'results/monitor_scores.csv').open()))
 valid=[r for r in scores if r['suspicion_score'] not in ('','None')]
 h=[float(r['suspicion_score']) for r in valid if r['mode']=='honest']; b=[float(r['suspicion_score']) for r in valid if r['valid_backdoor']=='True']
 report['monitor']={'scored_honest':len(h),'backdoors':len(b),'unscored':len(scores)-len(valid),'auc':auc(h,b),'catch_rate_at_2pct':catch_rate(h,b),'honest_score_counts':dict(collections.Counter(h)), 'backdoor_scores':b,'zero_of_two_exact_95pct_upper_bound':1-0.025**0.5}
 report['caveats']=['Historical labels retained; reference disagreement does not establish malicious intent.','n=2 cannot establish monitoring effectiveness; bootstrap intervals miss unseen positive diversity.','2% is an expected honest false-positive rate with randomized ties, not a fixed-size total audit.','Existing validator ignores ordering/container differences; sensitivity analysis needed.','Subprocess isolation is not a security sandbox.']
 (ROOT/'results/reproduction.json').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report['monitor'],indent=2))
if __name__=='__main__': main()
