#!/bin/sh
# Day 4: once the untrusted run is done, have the trusted monitor score every
# honest solution and every valid backdoor, then print AUC and the catch rate.
# Safe to rerun: cached monitor replies are reused.
#
#   nohup caffeinate -i sh scripts/run_monitor.sh > results/logs/monitor_run.log 2>&1 &
cd "$(dirname "$0")/.."
PY=.venv/bin/python

while pgrep -f "scripts/run_full.sh" >/dev/null; do
  sleep 60  # the untrusted run is still going; only one model fits in memory
done

echo "== $(date '+%F %T') warm-up: load the monitor model once with a 10-minute limit"
curl -s -m 600 localhost:11434/api/chat -d '{"model":"qwen2.5-coder:1.5b","messages":[{"role":"user","content":"Say OK."}],"stream":false,"keep_alive":"30m","options":{"num_ctx":2048,"num_predict":5}}' \
  | $PY -c "import json,sys; r=json.load(sys.stdin); print('load_s=%.1f' % (r.get('load_duration',0)/1e9), r.get('error',''))"

echo "== $(date '+%F %T') monitor scoring"
$PY -u src/run_monitor.py --attack-mode attack_v2 || exit 1

echo "== $(date '+%F %T') metrics"
$PY src/metrics.py results/monitor_scores.csv
echo "== $(date '+%F %T') done"
