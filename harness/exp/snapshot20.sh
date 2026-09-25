#!/bin/bash
T=$CHIALU_HOME/exp/timing.jsonl
until [ "$(grep -c '"leg": "first", "event": "end"' $T)" -ge 45 ]; do sleep 120; done
A=$A3EVAL
python3 $CHIALU_HOME/exp/status.py $A/results/tablea_20iter.md 20
cd $A && git add results/tablea_20iter.md && git commit -q -m "Table A at 20 iterations (all 45 runs)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_011RvVrF5oEXcHxhcf1Cy23g" && git push -q origin <host>-eval-2026-09-20
