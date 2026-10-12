#!/bin/sh
# Kindle Low-Power Sync Dashboard Script
# Runs on Kindle Linux (Root)

INTERVAL=1800
# 请将此地址修改为您自己部署的服务器 IP 或域名（例如：http://192.168.1.100:8085/screen.png）
SERVER_URL="http://your-server-ip:8085/screen.png"
TMP_IMG="/tmp/dashboard.png"
LOG_FILE="/mnt/us/dashboard.log"
LOCK_FILE="/tmp/dashboard.lock"
ONCE_LOCK="/tmp/dashboard_once.lock"
STOP_FILE="/mnt/us/stop_dashboard"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
    if [ $(wc -l < "$LOG_FILE" 2>/dev/null || echo 0) -gt 200 ]; then
        tail -n 100 "$LOG_FILE" > "$LOG_FILE.tmp" && mv "$LOG_FILE.tmp" "$LOG_FILE"
    fi
}

update_screen() {
    log "Starting refresh cycle..."
    
    # 防止系统原生屏保覆盖 & 关闭背光省电
    lipc-set-prop com.lab126.powerd preventScreenSaver 1 2>/dev/null
    lipc-set-prop com.lab126.powerd flIntensity 0 2>/dev/null
    
    # 1. 唤醒 Wi-Fi
    lipc-set-prop com.lab126.cmd wirelessEnable 1
    
    # 等待获取 IP（最多 15 秒）
    COUNT=0
    CONNECTED=0
    while [ $COUNT -lt 15 ]; do
        if ip route | grep -q default; then
            CONNECTED=1
            break
        fi
        sleep 1
        COUNT=$((COUNT + 1))
    done

    if [ $CONNECTED -eq 1 ]; then
        log "Wi-Fi connected. Fetching latest dashboard image..."
        # 2. 下载到唯一临时文件，防止并发踩踏
        TMP_DOWNLOAD="/tmp/dashboard_$$.png"
        curl -s -k -m 20 "$SERVER_URL" -o "$TMP_DOWNLOAD"
        
        # 3. 严格校验：文件大小必须大于 10KB 才是完整有效的图片！
        FILE_SIZE=$(wc -c < "$TMP_DOWNLOAD" 2>/dev/null || echo 0)
        if [ -s "$TMP_DOWNLOAD" ] && [ "$FILE_SIZE" -gt 10000 ]; then
            log "Image downloaded successfully (${FILE_SIZE} bytes). Refreshing screen..."
            mv -f "$TMP_DOWNLOAD" "$TMP_IMG"
            # 只有下载成功后才执行清屏，彻底杜绝白屏！
            eips -c
            sleep 1
            eips -g "$TMP_IMG"
            log "Screen refreshed."
        else
            log "Warning: Downloaded image is invalid or empty (${FILE_SIZE} bytes), keeping current screen."
            rm -f "$TMP_DOWNLOAD"
        fi
    else
        log "Error: Wi-Fi connection timed out, keeping current screen."
    fi

    # 4. 关闭 Wi-Fi 节省电量
    lipc-set-prop com.lab126.cmd wirelessEnable 0
    log "Wi-Fi turned off."
}

# 单次执行模式（严格防双击/连击并发锁）
if [ "$1" = "once" ]; then
    if [ -f "$ONCE_LOCK" ]; then
        PID=$(cat "$ONCE_LOCK" 2>/dev/null)
        if kill -0 "$PID" 2>/dev/null; then
            echo "Refresh already in progress (PID $PID), ignoring duplicate click."
            exit 0
        fi
    fi
    echo $$ > "$ONCE_LOCK"
    # 右下角给一个微小的即时反馈，告知正在刷新，避免误以为没反应
    eips 0 39 "Refreshing..." 2>/dev/null
    update_screen
    rm -f "$ONCE_LOCK"
    exit 0
fi

# 后台常驻模式
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if kill -0 "$PID" 2>/dev/null; then
        echo "Dashboard daemon is already running (PID $PID)."
        exit 0
    fi
fi

echo $$ > "$LOCK_FILE"
rm -f "$STOP_FILE"
log "Dashboard daemon started (PID $$), interval: ${INTERVAL}s."

while true; do
    if [ -f "$STOP_FILE" ]; then
        log "Stop signal detected. Exiting daemon."
        lipc-set-prop com.lab126.powerd preventScreenSaver 0 2>/dev/null
        rm -f "$STOP_FILE" "$LOCK_FILE"
        exit 0
    fi

    HOUR=$(date '+%H')
    if [ "$HOUR" -ge 23 ] || [ "$HOUR" -lt 6 ]; then
        log "Night hours detected. Entering extended sleep (2 hours)..."
        SLEEP_TIME=7200
    else
        update_screen
        SLEEP_TIME=$INTERVAL
    fi

    log "Suspending device for ${SLEEP_TIME} seconds..."
    if [ -e /sys/class/rtc/rtc1/wakealarm ]; then
        echo 0 > /sys/class/rtc/rtc1/wakealarm
        echo "+$SLEEP_TIME" > /sys/class/rtc/rtc1/wakealarm
        echo mem > /sys/power/state
    else
        rtcwake -d /dev/rtc1 -m mem -s "$SLEEP_TIME" 2>/dev/null || sleep "$SLEEP_TIME"
    fi
done