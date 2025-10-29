# 🧪 PKI Site Health Check

A set of bash scripts for checking the availability and correctness of public PKI services for ZETES / eID PKI (Estonia).

## 📂 Structure
- `pki_check.sh`: checks PDF, CRT, and CRL repositories
- `check_ocsp.sh`: checks the OCSP endpoint and certificate status
- `check_ldap.sh`: checks LDAP/LDAPS availability and performs queries
- `pki_monitor.sh`: a single orchestrator script with a final summary
- `artifacts/`: folder for downloaded artifacts (PDF, CRT, CRL)
- `results.csv`: consolidated CSV report with all results

## ⚙️ Requirements
- `bash`, `curl`, `openssl`, `ldap-utils`, `coreutils`
- Internet access to `*.eidpki.ee` services

## 🚀 Run
```bash
chmod +x *.sh
./pki_monitor.sh
```

### 🔑 Important for OCSP checks
For OCSP checks to work correctly, the following files must be present in the directory:

```text
./artifacts/crt/EEGovCA2025.crt
./artifacts/crt/ESTEID2025.crt
```

They are used as the issuer and cert when making a request to `https://ocsp.eidpki.ee`.

### 🧾 Example output
```text
📄 PDF:  9/9 OK
🔏 CRT:  2/2 OK
🚫 CRL:  2/2 OK
🧩 OCSP: 1/1 OK
📡 LDAP: 2 searches OK, 2 ports OK
✅ Check completed
```

All results are logged to `results.csv` and saved for subsequent analysis.

