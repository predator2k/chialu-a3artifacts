#!/bin/bash
# Run after topping up OpenRouter: every Table A run resumed to 70 real iterations, all in parallel.
source $CHIALU_HOME/chialu-env.sh >/dev/null 2>&1
export RAY_ADDRESS=<HEAD_IP>:6395
cd $CHIALU
E=$CHIALU_HOME/exp
python3 $E/recover.py --apply | while read job cmd; do
  ( echo "{\"job\": \"$job\", \"leg\": \"recover\", \"event\": \"start\", \"t\": $(date +%s)}" >> $E/timing.jsonl
    eval "${cmd%%#*}" >> $E/logs/$job.log 2>&1
    echo "{\"job\": \"$job\", \"leg\": \"recover\", \"event\": \"end\", \"t\": $(date +%s), \"rc\": $?}" >> $E/timing.jsonl ) &
done
wait
echo "RECOVER DONE" >> $E/logs/driver.log
