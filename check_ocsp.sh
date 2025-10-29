#!/usr/bin/env bash
set -Eeuo pipefail

OUT_DIR="${OUT_DIR:-./artifacts}"
LOG_CSV="${LOG_CSV:-./results.csv}"
CURL_OPTS=(--silent --show-error --location --max-time 15 --connect-timeout 5)

OCSP_URLS=(
  "https://ocsp.eidpki.ee"
)

CA_CERT="./artifacts/crt/ESTEID2025.crt"
TEST_CERT="./artifacts/crt/mycert.crt"

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
ensure_log() { [[ -f "$LOG_CSV" ]] || echo "timestamp,type,url,status,http_code,ms,filepath,sha256,note" > "$LOG_CSV"; }
log_csv() { echo "$@" >> "$LOG_CSV"; }

check_ocsp_http() {
  local url="$1"
  local start_ms end_ms dur_ms code
  echo "[$(ts)] Checking OCSP availability: $url"
  start_ms=$(($(date +%s%3N)))
  code="$(curl -I "${CURL_OPTS[@]}" -w "%{http_code}" -o /dev/null "$url" || echo 000)"
  end_ms=$(($(date +%s%3N))); dur_ms=$((end_ms - start_ms))
  log_csv "$(ts),ocsp_http_check,$url,$([[ "$code" == 200 || "$code" == 206 ]] && echo ok || echo fail),$code,$dur_ms,,," 
}

check_ocsp_status() {
  local url="$1"
  local tmpout status
  tmpout="$(mktemp)"
  echo "[$(ts)] Checking certificate OCSP status via $url"

  if [[ ! -f "$CA_CERT" || ! -f "$TEST_CERT" ]]; then
    echo "[$(ts)] ❌ Certificate not found: $CA_CERT or $TEST_CERT"
    return
  fi

  # For HTTPS OCSP add Host header and use -issuer / -cert
  if openssl ocsp \
      -issuer "$CA_CERT" \
      -cert "$TEST_CERT" \
      -url "$url" \
      -header "HOST=$(echo "$url" | awk -F/ '{print $3}')" \
      -resp_text -noverify -timeout 10 >"$tmpout" 2>&1; then

    grep -E "Cert Status|Response verify|Next Update|This Update" "$tmpout" | sed 's/^/  /'
    status="$(grep -E 'Cert Status' "$tmpout" | awk -F': ' '{print $2}' | tr -d '\r')"
    log_csv "$(ts),ocsp_status,$url,ok,200,0,,$(sha256sum "$tmpout" | awk '{print $1}'),${status}"
    echo "[$(ts)] ✅ OCSP response: $status"
  else
    echo "[$(ts)] ❌ OCSP request error ($url)"
    echo "--- openssl output ---"
    cat "$tmpout"
    echo "----------------------"
    log_csv "$(ts),ocsp_status,$url,fail,000,0,,,"
  fi

  rm -f "$tmpout"
}

main() {
  ensure_log
  for url in "${OCSP_URLS[@]}"; do
    check_ocsp_http "$url"
    check_ocsp_status "$url"
  done
}

main
