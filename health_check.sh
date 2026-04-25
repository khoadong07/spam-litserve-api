#!/bin/bash

if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

LOG_FILE="./health_check.log"
LOCK_FILE="/tmp/health_restart.lock"

send_telegram() {
  curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
    -d "chat_id=${TELEGRAM_CHAT_ID}" \
    -d "text=$1" \
    -d "parse_mode=HTML" > /dev/null
}

log() {
  echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

check_health() {
  status=$(curl -s -o /dev/null -w "%{http_code}" --max-time "$TIMEOUT" "$URL")

  if [ "$status" != "200" ]; then
    log "❌ FAIL $URL | status=$status"
    return 1
  fi

  log "✅ OK $URL | status=$status"
  return 0
}

restart_service() {
  if [ -f "$LOCK_FILE" ]; then
    log "⚠️ Restart skipped: lock exists"
    return
  fi

  touch "$LOCK_FILE"

  send_telegram "🚨 <b>Health check FAILED</b>%0AURL: <code>${URL}</code>%0AĐợi ${RESTART_DELAY}s rồi restart"

  sleep "$RESTART_DELAY"

  log "🔁 Restarting service..."
  bash stop.sh
  sleep 3

  if bash start_background.sh; then
    log "✅ start_background.sh success"
  else
    log "❌ start_background.sh failed"
    send_telegram "❌ <b>Restart FAILED</b>%0AURL: <code>${URL}</code>"
    rm -f "$LOCK_FILE"
    return
  fi

  sleep 10

  if check_health; then
    log "✅ Service recovered"
    send_telegram "✅ <b>Restart SUCCESS</b>%0AURL: <code>${URL}</code>%0AService healthy again"
  else
    log "❌ Still unhealthy after restart"
    send_telegram "❌ <b>Restart done but still FAIL</b>%0AURL: <code>${URL}</code>"
  fi

  rm -f "$LOCK_FILE"
}

while true; do
  if ! check_health; then
    restart_service
  fi

  sleep "$CHECK_INTERVAL"
done