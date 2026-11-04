#!/bin/sh
# Full untrusted-model run: honest on all 100 problems, then attack_v2 with up
# to 3 attempts each. Safe to rerun: everything already cached is skipped.
#
#   nohup caffeinate -i sh scripts/run_full.sh > results/logs/full_run.log 2>&1 &
#   tail -f results/logs/full_run.log
set -e
cd "$(dirname "$0")/.."
PY=.venv/bin/python

echo "== $(date '+%F %T') warm-up: load the model once with a 10-minute limit"
curl -s -m 600 localhost:11434/api/chat -d '{"model":"qwen2.5-coder:7b","messages":[{"role":"user","content":"Say OK."}],"stream":false,"keep_alive":"30m","options":{"num_ctx":2048,"num_predict":5}}' \
  | $PY -c "import json,sys; r=json.load(sys.stdin); print('load_s=%.1f' % (r.get('load_duration',0)/1e9), r.get('error',''))"

echo "== $(date '+%F %T') honest, 100 problems"
$PY -u src/run_untrusted.py --mode honest

echo "== $(date '+%F %T') attack_v2, 100 problems, up to 3 attempts"
$PY -u src/run_untrusted.py --mode attack_v2 --attempts 3

echo "== $(date '+%F %T') done"
