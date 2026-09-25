#!/bin/bash
# Every hour until the Table A driver finishes: refresh results/tablea_status.md and commit+push it.
A=$A3EVAL
while true; do
  python3 $CHIALU_HOME/exp/status.py > /dev/null 2>&1
  cd $A && git add results/tablea_status.md && git commit -q -m "Table A progress $(date +%H:%M)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_011RvVrF5oEXcHxhcf1Cy23g" && git push -q origin <host>-eval-2026-09-20
  grep -q "ALL DONE" $CHIALU_HOME/exp/logs/driver.log 2>/dev/null && break
  sleep 3600
done
