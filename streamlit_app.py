#!/usr/bin/env python3
"""
Streamlit UI for PKI Site Health Check

Provides a simple web interface to run checks, view summaries,
and explore the latest results from the CSV log.
"""

import csv
from pathlib import Path
from typing import Dict, List
import mimetypes
import os

import streamlit as st
import hashlib

from pki_monitor import PKIMonitor
from ocsp_checker import OCSPChecker


def render_summary(monitor: PKIMonitor):
    pdf_results = [r for r in monitor.results if str(r.get("type", "")).startswith("pdf_")]
    crt_results = [r for r in monitor.results if str(r.get("type", "")).startswith("crt_")]
    crl_results = [r for r in monitor.results if str(r.get("type", "")).startswith("crl_")]
    ocsp_results = [r for r in monitor.results if str(r.get("type", "")).startswith("ocsp_")]
    ldap_search_results = [r for r in monitor.results if r.get("type") == "ldap_search"]
    ldap_port_results = [r for r in monitor.results if r.get("type") == "ldap_port"]

    pdf_ok = len([r for r in pdf_results if r.get("status") == "ok"])
    crt_ok = len([r for r in crt_results if r.get("status") == "ok"])
    crl_ok = len([r for r in crl_results if r.get("status") == "ok"])
    ocsp_ok = len([r for r in ocsp_results if r.get("status") == "ok"])
    ldap_search_ok = len([r for r in ldap_search_results if r.get("status") == "ok"])
    ldap_port_ok = len([r for r in ldap_port_results if r.get("status") == "ok"])

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("PDF", f"{pdf_ok}/{len(pdf_results)} OK")
        st.metric("CRT", f"{crt_ok}/{len(crt_results)} OK")
    with col2:
        st.metric("CRL", f"{crl_ok}/{len(crl_results)} OK")
        st.metric("OCSP", f"{ocsp_ok}/{len(ocsp_results)} OK")
    with col3:
        st.metric("LDAP searches", f"{ldap_search_ok}")
        st.metric("LDAP ports", f"{ldap_port_ok}")


def list_artifacts(artifacts_path: Path) -> Dict[str, List[Path]]:
    """Return a dict of {type: [file_path]} for pdf, crl, crt."""
    types = ["pdf", "crl", "crt"]
    file_dict = {}
    for t in types:
        d = artifacts_path / t
        if d.exists() and d.is_dir():
            file_dict[t] = [f for f in d.iterdir() if f.is_file()]
        else:
            file_dict[t] = []
    return file_dict

def clear_artifacts(artifacts_path: Path):
    types = ["pdf", "crl", "crt"]
    # Files to keep (for testing)
    whitelist = {"mycert.crt", "EEGovCA2025.crt", "ESTEID2025.crt"}
    for t in types:
        d = artifacts_path / t
        if d.exists() and d.is_dir():
            for f in d.iterdir():
                if f.is_file():
                    if t == "crt" and f.name in whitelist:
                        continue
                    try:
                        f.unlink()
                    except Exception as e:
                        print(f"Failed to delete {f}: {e}")


def main():
    st.set_page_config(page_title="PKI Monitor", page_icon="🧪", layout="wide")
    # --- Basic auth gate (very simple; for private deployments only) ---
    # Try to get from Streamlit secrets first, fallback to environment variables or defaults
    try:
        auth_config = st.secrets.get("auth", {})
        USER = auth_config.get("username", "admin")
        PASSWORD_HASH = auth_config.get("password_hash", "")
        
        # If password_hash is empty, generate it from password field if available
        if not PASSWORD_HASH and "password" in auth_config:
            PASSWORD_HASH = hashlib.sha256(auth_config["password"].encode()).hexdigest()
        
        # If still empty, use default hash
        if not PASSWORD_HASH:
            PASSWORD_HASH = hashlib.sha256("secret123".encode()).hexdigest()
    except Exception:
        # Fallback to environment variables or defaults
        USER = os.environ.get("PKI_UI_USER", "admin")
        PASSWORD_HASH = os.environ.get(
            "PKI_UI_PASSWORD_HASH",
            hashlib.sha256("secret123".encode()).hexdigest(),
        )

    st.title("🧪 PKI Site Health Check")
    st.caption("Monitor ZETES / eID PKI services")

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.subheader("🔐 Private Access")
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            if username == USER and hashlib.sha256(password.encode()).hexdigest() == PASSWORD_HASH:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Invalid credentials")
        st.stop()

    with st.sidebar:
        st.header("Settings")
        artifacts_dir = st.text_input("Artifacts directory", value="./artifacts")
        log_csv = st.text_input("CSV log file", value="./results.csv")
        st.markdown("---")
        run_checks = st.button("Run all checks", type="primary")
        st.markdown("---")
        if st.button("Clear all artifacts", type="secondary"):
            clear_artifacts(Path(artifacts_dir).resolve())
            st.success("Artifacts cleared. Reload to refresh file lists.")
        if st.button("Clear log", type="secondary"):
            log_path_sidebar = Path(log_csv).resolve()
            if log_path_sidebar.exists():
                log_path_sidebar.unlink()
                # Clear session state when log is cleared
                if 'monitor_results' in st.session_state:
                    st.session_state.monitor_results = None
                st.success("Log cleared. Reload to refresh.")
            else:
                st.info("No log file found.")

    log_path = Path(log_csv).resolve()
    artifacts_path = Path(artifacts_dir).resolve()
    
    # Get artifact files list for UI
    artifact_files = list_artifacts(artifacts_path)

    # Initialize session state for storing check results
    if 'monitor_results' not in st.session_state:
        st.session_state.monitor_results = None
    if 'last_artifacts_path' not in st.session_state:
        st.session_state.last_artifacts_path = None
    if 'last_log_path' not in st.session_state:
        st.session_state.last_log_path = None
    
    # Clear results if paths have changed
    if (st.session_state.last_artifacts_path != str(artifacts_path) or 
        st.session_state.last_log_path != str(log_path)):
        st.session_state.monitor_results = None
        st.session_state.last_artifacts_path = str(artifacts_path)
        st.session_state.last_log_path = str(log_path)

    if run_checks:
        with st.status("Running checks...", expanded=True) as status:
            monitor = PKIMonitor(str(artifacts_path), str(log_path))
            ok = monitor.run_all_checks()
            status.update(label="Checks completed" if ok else "Checks finished with issues", state="complete")
        
        # Store results in session state
        st.session_state.monitor_results = monitor

    # Display summary and results from session state (persists across OCSP checks)
    if st.session_state.monitor_results is not None:
        st.subheader("Summary")
        render_summary(st.session_state.monitor_results)

        st.subheader("Session results")
        st.dataframe(st.session_state.monitor_results.results, use_container_width=True, hide_index=True)

    # Track if we should keep the OCSP expander open
    if 'ocsp_expander_open' not in st.session_state:
        st.session_state.ocsp_expander_open = False
    
    with st.expander("Manual OCSP Check...", expanded=st.session_state.ocsp_expander_open):
        st.caption("Check certificate status using OCSP with a serial number")
        
        # Get available issuer certificates
        crt_files = artifact_files.get("crt", [])
        issuer_options = [str(f.resolve()) for f in crt_files if f.suffix in ['.crt', '.pem']]
        
        if issuer_options:
            col1, col2 = st.columns([3, 1])
            
            with col1:
                selected_issuer = st.selectbox(
                    "Issuer Certificate",
                    issuer_options,
                    help="Select the CA/issuer certificate file"
                )
                serial_number = st.text_input(
                    "Serial Number",
                    placeholder="0x12c9a92ef05c17c292e09f56aa3d1cc5997e219f",
                    help="Enter the serial number in hex format (with or without 0x prefix)"
                )
            
            with col2:
                ocsp_url = st.text_input(
                    "OCSP URL",
                    value="https://ocsp.eidpki.ee/",
                    help="OCSP server URL"
                )
                st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            
            if st.button("Check OCSP Status", type="primary"):
                st.session_state.ocsp_expander_open = True
                if serial_number.strip():
                    with st.status("Checking OCSP status...", expanded=True) as status:
                        try:
                            # Ensure serial has 0x prefix if it's hex
                            serial = serial_number.strip()
                            if not serial.startswith('0x'):
                                serial = '0x' + serial
                            
                            ocsp_checker = OCSPChecker(str(artifacts_path), str(log_path))
                            result = ocsp_checker.check_ocsp_by_serial(ocsp_url, selected_issuer, serial)
                            
                            # Log the result
                            with open(log_path, 'a', newline='') as f:
                                writer = csv.writer(f)
                                writer.writerow([
                                    result.get('timestamp', ''),
                                    result.get('type', ''),
                                    result.get('url_or_host', ''),
                                    result.get('status', ''),
                                    result.get('http_code_or_port', ''),
                                    result.get('ms', ''),
                                    result.get('sha256_or_note', ''),
                                    result.get('note', '')
                                ])
                            
                            status.update(label="OCSP check completed", state="complete")
                            
                            # Display result
                            if result.get('status') == 'ok':
                                st.success(f"✅ OCSP Response: {result.get('note', 'Unknown')}")
                            else:
                                st.error(f"❌ OCSP check failed: {result.get('note', 'Unknown error')}")
                            
                            # Show full result details
                            st.json(result)
                            
                        except Exception as e:
                            status.update(label="OCSP check failed", state="error")
                            st.error(f"Error: {e}")
                else:
                    st.warning("Please enter a serial number")
        else:
            st.info("⚠️ No issuer certificates found. Download CRT files first by running checks.")
    
    st.markdown("---")
    
    st.subheader("Downloaded Artifacts")
    tabs = st.tabs(["PDF", "CRL", "CRT"])
    for i, t in enumerate(["pdf", "crl", "crt"]):
        with tabs[i]:
            files = artifact_files[t]
            if files:
                for file in files:
                    fn = file.name
                    mime, _ = mimetypes.guess_type(str(file))
                    mime = mime or "application/octet-stream"
                    try:
                        with open(file, "rb") as f:
                            st.download_button(
                                label=f"Download {fn}",
                                data=f.read(),
                                file_name=fn,
                                mime=mime
                            )
                    except Exception as e:
                        st.error(f"Failed to offer {fn}: {e}")
            else:
                st.info(f"No {t.upper()} artifacts found.")


if __name__ == "__main__":
    main()


