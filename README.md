# 🧪 PKI Site Health Check

## 🚀 Quickstart (Streamlit Cloud)

**TL;DR for Streamlit Cloud:**
- This app checks the health of Estonian eID PKI services.
- It downloads and scans certificates, CRLs, OCSP endpoints, and LDAP services.
- All results and artifacts are visible and downloadable through a friendly web UI.
- You can run this on [streamlit.io/cloud](https://streamlit.io/cloud) or locally.

**How to run on Streamlit Cloud:**
1. **Upload the project to [streamlit.app](https://streamlit.app/).**
2. Ensure your `requirements.txt` includes `streamlit>=1.36.0` (already included).
3. Set the main file to `streamlit_app.py` in Streamlit Cloud settings.
4. Press "Deploy".

**App Usage:**
- The sidebar lets you choose or create the artifacts directory and the results CSV log file.
- Press "Run all checks" to analyze PKI endpoints. Artifacts (PDF, CRT, CRL) and CSV logs will be generated and can be viewed/downloaded from the UI.
- You may clear all artifacts any time with the sidebar button (with a whitelist for test certificates).
- See live tables, summaries, and charts of your latest checks.

---

# Original README follows

A Python command line application for checking the availability and correctness of public PKI services for ZETES / eID PKI (Estonia).

This project has been converted from bash scripts to a unified Python CLI application for better maintainability and cross-platform compatibility.

## 📂 Structure
- `pki_monitor.py`: Main CLI application and orchestrator
- `pki_checker.py`: Handles PDF, CRT, and CRL repository checks
- `ocsp_checker.py`: Handles OCSP endpoint and certificate status checks
- `ldap_checker.py`: Handles LDAP/LDAPS availability and query testing
- `artifacts/`: Folder for downloaded artifacts (PDF, CRT, CRL)
    - **NOTE:** The files `mycert.crt`, `EEGovCA2025.crt`, and `ESTEID2025.crt` are whitelist-protected for testing and WILL NOT be deleted by the "Clear all artifacts" function in the app sidebar.
- `results.csv`: Consolidated CSV report with all results
- `requirements.txt`: Python dependencies
- `setup.py`: Installation script

## ⚙️ Requirements
- Python 3.7 or higher
- `openssl` (for OCSP checks)
- Python package `ldap3` (installed via `requirements.txt`)
- Internet access to `*.eidpki.ee` services

## 🚀 Installation

### Option 1: Direct Python execution
```bash
# Clone or download the project
cd pki-monitor-py

# Install dependencies (optional - uses only standard library)
pip install -r requirements.txt

# Make executable
chmod +x pki_monitor.py
```

### Option 2: Install as package
```bash
# Install in development mode
pip install -e .

# Or install normally
pip install .
```

## 🚀 Usage

### Basic Usage
```bash
# Run all checks with default settings
python pki_monitor.py

# Or if installed as package
pki-monitor
```

### Streamlit UI
```bash
# Install dependencies (includes Streamlit)
pip install -r requirements.txt

# Launch the web UI
streamlit run streamlit_app.py
```
The UI lets you configure the artifacts directory and CSV log file, run checks, view a live summary, and browse/download the latest results.

Note: LDAP checks now use the pure-Python `ldap3` library (no system `ldapsearch`/`ldap-utils` required), which runs on Streamlit Cloud.

#### Optional: Simple UI authentication
The app includes a very basic username/password gate suitable for private demos. Configure via environment variables (or keep defaults `admin` / `secret123`).

```bash
export PKI_UI_USER="admin"
export PKI_UI_PASSWORD_HASH="$(python - <<'PY'
import hashlib
print(hashlib.sha256("secret123".encode()).hexdigest())
PY
)"
streamlit run streamlit_app.py
```
Security note: This is minimal. For production, use Streamlit Cloud access controls or a proper auth proxy.

### Advanced Usage
```bash
# Use custom artifacts directory
python pki_monitor.py --artifacts ./data

# Use custom log file
python pki_monitor.py --log results.log

# Show only summary from existing log (without running new checks)
python pki_monitor.py --summary-only

# Show more lines from log
python pki_monitor.py --lines 50

# Get help
python pki_monitor.py --help
```

### Command Line Options
- `--artifacts DIR`: Directory to store downloaded artifacts (default: ./artifacts)
- `--log FILE`: CSV log file for results (default: ./results.csv)
- `--summary-only`: Show summary from existing log file without running new checks
- `--lines N`: Number of last lines to show from log (default: 20)
- `--help`: Show help message

## 🔑 Important for OCSP checks
For OCSP checks to work correctly, the following files must be present in the artifacts directory:

```text
./artifacts/crt/ESTEID2025.crt  # CA certificate (issuer)
./artifacts/crt/mycert.crt      # Test certificate
```

These certificates are used when making OCSP requests to `https://ocsp.eidpki.ee`. The application will automatically download the required certificates during the first run.

## 🧾 Example Output
```text
[2025-01-27T10:30:00Z] 🚀 Starting PKI checks...
----------------------------------------
[2025-01-27T10:30:00Z] ▶ Running PDF/CRT/CRL checks
----------------------------------------
[2025-01-27T10:30:01Z] Checking [pdf]: https://repository.eidpki.ee/static/...
[2025-01-27T10:30:01Z] ✅ pdf accessible: HTTP 200 (150ms)
[2025-01-27T10:30:02Z] ✅ pdf saved: ./artifacts/pdf/20250127T103002Z-Root CP_V 1.1.pdf (sha256=abc123...)
...
----------------------------------------
[2025-01-27T10:30:05Z] ▶ Running OCSP checks
----------------------------------------
[2025-01-27T10:30:05Z] Checking OCSP availability: https://ocsp.eidpki.ee
[2025-01-27T10:30:05Z] ✅ OCSP HTTP: 200 (120ms)
[2025-01-27T10:30:06Z] ✅ OCSP response: good
...
----------------------------------------
[2025-01-27T10:30:08Z] ▶ Running LDAP checks
----------------------------------------
[2025-01-27T10:30:08Z] Checking port 389 on ldap.eidpki.ee
[2025-01-27T10:30:08Z] ✅ Port 389 is open (45ms)
[2025-01-27T10:30:09Z] ✅ Entry found: dn: cn=test,dc=ldap,dc=eidpki,dc=ee
...

[2025-01-27T10:30:10Z] 📊 Results summary:
----------------------------------------
📄 PDF:  9/9 OK
🔏 CRT:  2/2 OK
🚫 CRL:  2/2 OK
🧩 OCSP: 1/1 OK
📡 LDAP: 2 searches OK, 2 ports OK
----------------------------------------
[2025-01-27T10:30:10Z] ✅ Checks completed
```

All results are logged to `results.csv` and saved for subsequent analysis.

## 📊 CSV Output Format
The application generates a CSV file with the following columns:
- `timestamp`: UTC timestamp in ISO format
- `type`: Type of check (pdf_check, pdf_download, crt_check, etc.)
- `url_or_host`: URL or hostname being checked
- `status`: Result status (ok/fail)
- `http_code_or_port`: HTTP response code or port number
- `ms`: Response time in milliseconds
- `filepath_or_note`: Local file path or additional note
- `sha256_or_note`: SHA256 hash or additional note
- `note`: Additional information or error details

## 🔧 Development

### Running Tests
```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Run with coverage
pytest --cov=pki_monitor
```

### Code Quality
```bash
# Format code
black pki_monitor.py pki_checker.py ocsp_checker.py ldap_checker.py

# Lint code
flake8 pki_monitor.py pki_checker.py ocsp_checker.py ldap_checker.py

# Type checking
mypy pki_monitor.py pki_checker.py ocsp_checker.py ldap_checker.py
```

## 🆚 Migration from Bash Scripts
The Python version provides the same functionality as the original bash scripts with these improvements:
- **Cross-platform compatibility**: Works on Windows, macOS, and Linux
- **Better error handling**: More detailed error messages and graceful failure handling
- **Unified interface**: Single command with multiple options instead of separate scripts
- **Enhanced logging**: Structured CSV output with more detailed information
- **Modular design**: Easy to extend and maintain
- **No external dependencies**: Uses only Python standard library (except for system tools)

### Original Script Mapping
- `pki_monitor.sh` → `pki_monitor.py` (main orchestrator)
- `pki_check.sh` → `pki_checker.py` (PDF/CRT/CRL checks)
- `check_ocsp.sh` → `ocsp_checker.py` (OCSP checks)
- `check_ldap.sh` → `ldap_checker.py` (LDAP checks)
