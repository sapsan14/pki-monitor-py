#!/usr/bin/env bash
set -Eeuo pipefail

# === Settings ===
LOG_CSV="./results.csv"
ARTIFACTS_DIR="./artifacts"
SCRIPTS=(pki_check.sh check_ocsp.sh check_ldap.sh)

ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

# === Check presence of sub-scripts ===
for s in "${SCRIPTS[@]}"; do
  [[ -x "$s" ]] || { echo "❌ Script $s not found or not executable"; exit 1; }
done

# === Create artifacts and log ===
mkdir -p "$ARTIFACTS_DIR"
[[ -f "$LOG_CSV" ]] || echo "timestamp,type,url_or_host,status,http_code_or_port,ms,filepath_or_note,sha256_or_note,note" > "$LOG_CSV"

# === Run all checks ===
echo "[$(ts)] 🚀 Starting PKI checks..."
for s in "${SCRIPTS[@]}"; do
  echo "----------------------------------------"
  echo "[$(ts)] ▶ Running $s"
  echo "----------------------------------------"
  "./$s" || echo "⚠️ $s finished with an error"
done

# === CSV summary ===
echo
echo "[$(ts)] 📊 Results summary:"
echo "----------------------------------------"

total_pdf=$(grep -c "pdf_download" "$LOG_CSV" || true)
ok_pdf=$(grep "pdf_download" "$LOG_CSV" | grep -c ",ok," || true)

total_crt=$(grep -c "crt_download" "$LOG_CSV" || true)
ok_crt=$(grep "crt_download" "$LOG_CSV" | grep -c ",ok," || true)

total_crl=$(grep -c "crl_download" "$LOG_CSV" || true)
ok_crl=$(grep "crl_download" "$LOG_CSV" | grep -c ",ok," || true)

total_ocsp=$(grep -c "ocsp_status" "$LOG_CSV" || true)
ok_ocsp=$(grep "ocsp_status" "$LOG_CSV" | grep -c ",ok," || true)

ldap_ok=$(grep "ldap_search" "$LOG_CSV" | grep -c ",ok," || true)
ldap_ports_ok=$(grep "ldap_port" "$LOG_CSV" | grep -c ",ok," || true)

printf "📄 PDF:  %s/%s OK\n" "$ok_pdf" "$total_pdf"
printf "🔏 CRT:  %s/%s OK\n" "$ok_crt" "$total_crt"
printf "🚫 CRL:  %s/%s OK\n" "$ok_crl" "$total_crl"
printf "🧩 OCSP: %s/%s OK\n" "$ok_ocsp" "$total_ocsp"
printf "📡 LDAP: %s searches OK, %s ports OK\n" "$ldap_ok" "$ldap_ports_ok"

echo "----------------------------------------"
echo "[$(ts)] ✅ Checks completed"

# === Show last results ===
echo
echo "[$(ts)] 📋 Last 20 lines of the report:"
echo "----------------------------------------"

if command -v column >/dev/null; then
  tail -n 20 "$LOG_CSV" | column -s, -t | less -SFX
else
  tail -n 20 "$LOG_CSV"
fi
