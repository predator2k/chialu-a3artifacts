#!/bin/bash
# Every 20 minutes until Table A finishes: drop compile intermediates from the Verilator build cache
# (finished builds only; a directory still compiling is named <key>.build-<pid>).
C=$CHIALU_HOME/.cache/chialu/sim_build
while true; do
  find $C -mindepth 3 -maxdepth 3 -type f \( -name '*.gch' -o -name '*.o' -o -name '*.a' -o -name '*.d' -o -name '*.cpp' -o -name '*.h' -o -name '*.mk' -o -name '*.dat' \) -print0 2>/dev/null | grep -zv '\.build-' | xargs -0 -r rm -f
  $CHIALU_HOME/exp/clean_<host>_cache.sh
  echo "$(date +%H:%M) $(df -h /data2 | tail -1 | awk '{print $4}') free, cache $(du -sh $C 2>/dev/null | cut -f1)"
  grep -q "ALL DONE" $CHIALU_HOME/exp/logs/driver.log 2>/dev/null && break
  sleep 1200
done
