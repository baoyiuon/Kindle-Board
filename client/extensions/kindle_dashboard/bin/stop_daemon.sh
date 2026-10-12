#!/bin/sh
# Signal dashboard daemon to stop
touch /mnt/us/stop_dashboard
lipc-set-prop com.lab126.powerd preventScreenSaver 0 2>/dev/null
if [ -f /tmp/dashboard.lock ]; then
    PID=$(cat /tmp/dashboard.lock)
    kill -9 "$PID" 2>/dev/null
    rm -f /tmp/dashboard.lock
fi