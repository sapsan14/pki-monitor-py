#!/usr/bin/env bash
set -Eeuo pipefail

OUT_DIR="${OUT_DIR:-./artifacts}"
LOG_CSV="${LOG_CSV:-./results.csv}"
CURL_OPTS=(--silent --show-error --location --max-time 60 --connect-timeout 10)

# === PDF documents ===
PDF_URLS=(
  "https://repository.eidpki.ee/static/Root%20CP_V%201.1%20-%20signed%2030.05.2025.pdf"
  "https://repository.eidpki.ee/static/Root%20CP_V%201.1%20-%20signed%2030.05.2025.pdf"
  "https://repository.eidpki.ee/static/2025%2010%2003%20-%20ZE%20CPS-ID1-ROOT-CA%20v1.3%20-%20Approved.pdf"
  "https://repository.eidpki.ee/static/2025%2010%2001%20-%20ZE%20CPS-ID1-EID-CA%20v1.3%20-%20Approved.pdf"
  "https://repository.eidpki.ee/static/2025%2010%2003%20-%20ZE%20TSPS-ID1%20v1.3%20-%20Approved.pdf"
  "https://repository.eidpki.ee/static/2025%2010%2003%20-%20ZE%20TC-ID1%20v1.3%20-%20Approved.pdf"
  "https://repository.eidpki.ee/static/2025%2010%2003%20-%20ZE%20TC-ID1-SUB%20v1.3%20-%20Approved.pdf"
  "https://repository.eidpki.ee/static/2025-10-03-ze-tc-id1-sub-v1.3_PBGB_Estonian%20Approved.pdf"
  "https://repository.eidpki.ee/static/Technical%20profile%20of%20certificates%20OCSP%20responses%20and%20CRLs_20251001_withoutUAT.pdf"
)

# === Certificates ===
CRT_URLS=(
  "https://crt.eidpki.ee/EEGovCA2025.crt"
  "https://crt.eidpki.ee/ESTEID2025.crt"
)

# === CRL files ===
CRL_URLS=(
  "https://crl.eidpki.ee/EEGovCA2025.crl"
  "https://crl.eidpki.ee/ESTEID2025.crl"
)

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
ensure_dirs() {
  mkdir -p "$OUT_DIR/pdf" "$OUT_DIR/crt" "$OUT_DIR/crl"
  [[ -f "$LOG_CSV" ]] || echo "timestamp,type,url,status,http_code,ms,filepath,sha256,note" > "$LOG_CSV"
}
log_csv() { echo "$@" >> "$LOG_CSV"; }

download_file() {
  local url="$1" ftype="$2" dir="$3"
  local tmpfile headers base file http_code ctype sha256 start_ms end_ms dur_ms

  echo "[$(ts)] Checking [$ftype]: $url"
  tmpfile="$(mktemp)"
  headers="$(mktemp)"
  base="$(basename "${url%%[\?#]*}")"
  file="$dir/$(date -u +%Y%m%dT%H%M%SZ)-$base"

  start_ms=$(($(date +%s%3N)))
  if ! curl -I "${CURL_OPTS[@]}" "$url" -D "$headers" -o /dev/null; then
    echo "[$(ts)] HEAD did not respond, trying partial GET"
    curl --range 0-512 "${CURL_OPTS[@]}" "$url" -D "$headers" -o "$tmpfile" || true
  fi
  http_code="$(grep -m1 -oE 'HTTP/[0-9.]+ [0-9]+' "$headers" | awk '{print $2}' || echo 000)"
  ctype="$(grep -i '^Content-Type:' "$headers" | head -n1 | cut -d' ' -f2- | tr -d '\r' || echo unknown)"
  end_ms=$(($(date +%s%3N))); dur_ms=$((end_ms - start_ms))
  log_csv "$(ts),${ftype}_check,$url,$([[ "$http_code" == 200 || "$http_code" == 206 ]] && echo ok || echo fail),$http_code,$dur_ms,,," 

  # Download the full file
  if curl "${CURL_OPTS[@]}" -o "$file" "$url"; then
    sha256="$(sha256sum "$file" | awk '{print $1}')"
    log_csv "$(ts),${ftype}_download,$url,ok,200,$dur_ms,$file,$sha256,"
    echo "[$(ts)] ✅ $ftype saved: $file (sha256=$sha256)"
  else
    log_csv "$(ts),${ftype}_download,$url,fail,000,$dur_ms,,,"
    echo "[$(ts)] ❌ Download error for $ftype"
  fi

  rm -f "$tmpfile" "$headers"
}

main() {
  ensure_dirs
  for url in "${PDF_URLS[@]}"; do download_file "$url" "pdf" "$OUT_DIR/pdf"; done
  for url in "${CRT_URLS[@]}"; do download_file "$url" "crt" "$OUT_DIR/crt"; done
  for url in "${CRL_URLS[@]}"; do download_file "$url" "crl" "$OUT_DIR/crl"; done
}

main
