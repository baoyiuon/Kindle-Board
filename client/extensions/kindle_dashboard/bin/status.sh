#!/bin/sh
# Show status via eips
BATTERY=$(gasgauge-info -c 2>/dev/null || cat /sys/devices/system/yoshi_battery/yoshi_battery0/battery_capacity 2>/dev/null || echo "Unknown")
RUNNING="未运行"
if [ -f /tmp/dashboard.lock ]; then
    PID=$(cat /tmp/dashboard.lock)
    if kill -0 "$PID" 2>/dev/null; then
        RUNNING="运行中 (PID $PID)"
    fi
fi

MSG="看板状态: $RUNNING | 当前电量: $BATTERY"
eips 0 39 "$MSG"
