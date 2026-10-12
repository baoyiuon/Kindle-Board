#!/bin/sh
# Start background low-power daemon
rm -f /mnt/us/stop_dashboard
nohup /bin/sh /mnt/us/dashboard.sh > /dev/null 2>&1 &
