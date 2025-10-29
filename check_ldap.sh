#!/usr/bin/env bash
set -Eeuo pipefail

LOG_CSV="${LOG_CSV:-./results.csv}"
LDAP_HOST="ldap.eidpki.ee"
LDAP_BASE="dc=ldap,dc=eidpki,dc=ee"
LDAP_FILTER="(objectClass=*)"
TIMEOUT=10

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
ensure_log() { [[ -f "$LOG_CSV" ]] || echo "timestamp,type,host,port,status,ms,note" > "$LOG_CSV"; }
log_csv() { echo "$@" >> "$LOG_CSV"; }

check_port() {
  local host="$1" port="$2"
  echo "[$(ts)] Checking port $port on $host"
  local start_ms end_ms dur_ms
  start_ms=$(($(date +%s%3N)))
  if timeout "$TIMEOUT" bash -c "echo > /dev/tcp/$host/$port" 2>/dev/null; then
    end_ms=$(($(date +%s%3N))); dur_ms=$((end_ms - start_ms))
    echo "[$(ts)] ✅ Port $port is open ($dur_ms ms)"
    log_csv "$(ts),ldap_port,$host,$port,ok,$dur_ms,"
  else
    echo "[$(ts)] ❌ Port $port is closed"
    log_csv "$(ts),ldap_port,$host,$port,fail,0,"
  fi
}

check_ldap_query() {
  local proto="$1"
  echo "[$(ts)] Checking LDAP query via $proto://$LDAP_HOST ..."
  local start_ms end_ms dur_ms res

  start_ms=$(($(date +%s%3N)))

  # LDAPS sometimes requires disabling CA verification
  if [[ "$proto" == "ldaps" ]]; then
    export LDAPTLS_REQCERT=never
  fi

  if res=$(ldapsearch -x -H "$proto://$LDAP_HOST" \
      -b "$LDAP_BASE" -s one "$LDAP_FILTER" cn 2>/dev/null | head -n 10); then
    end_ms=$(($(date +%s%3N))); dur_ms=$((end_ms - start_ms))
    if echo "$res" | grep -q "^dn:"; then
      local dn_line
      dn_line=$(echo "$res" | grep '^dn:' | head -n1)
      echo "[$(ts)] ✅ Entry found: $dn_line"
      log_csv "$(ts),ldap_search,$proto://$LDAP_HOST,ok,${proto^^},$dur_ms,found"
    else
      echo "[$(ts)] ⚠️ Response received, but no entries found"
      log_csv "$(ts),ldap_search,$proto://$LDAP_HOST,ok,${proto^^},$dur_ms,empty"
    fi
  else
    end_ms=$(($(date +%s%3N))); dur_ms=$((end_ms - start_ms))
    echo "[$(ts)] ❌ ldapsearch error"
    log_csv "$(ts),ldap_search,$proto://$LDAP_HOST,fail,${proto^^},$dur_ms,error"
  fi
}

main() {
  ensure_log
  check_port "$LDAP_HOST" 389
  check_port "$LDAP_HOST" 636
  check_ldap_query ldap
  check_ldap_query ldaps
}

main
