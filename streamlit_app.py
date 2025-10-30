#!/usr/bin/env python3
"""
Streamlit UI for PKI Site Health Check

Provides a simple web interface to run checks, view summaries,
and explore the latest results from the CSV log.
"""

import csv
from io import StringIO
from pathlib import Path
from typing import Dict, List
import mimetypes
import os

import streamlit as st

from pki_monitor import PKIMonitor


def read_csv_as_dicts(csv_path: Path, max_rows: int | None = None) -> List[Dict[str, str]]:
    if not csv_path.exists():
        return []
    rows: List[Dict[str, str]] = []
    with open(csv_path, "r", newline="") as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            rows.append(row)
            if max_rows is not None and idx + 1 >= max_rows:
                break
    return rows


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
    st.title("🧪 PKI Site Health Check")
    st.caption("Monitor ZETES / eID PKI services")

    with st.sidebar:
        st.header("Settings")
        artifacts_dir = st.text_input("Artifacts directory", value="./artifacts")
        log_csv = st.text_input("CSV log file", value="./results.csv")
        last_n = st.slider("Show last N rows", min_value=5, max_value=200, value=50, step=5)
        st.markdown("---")
        run_checks = st.button("Run all checks", type="primary")
        show_summary_only = st.button("Load summary from existing log")
        st.markdown("---")
        if st.button("Clear all artifacts", type="secondary"):
            clear_artifacts(Path(artifacts_dir).resolve())
            st.success("Artifacts cleared. Reload to refresh file lists.")

    log_path = Path(log_csv).resolve()
    artifacts_path = Path(artifacts_dir).resolve()

    if run_checks:
        with st.status("Running checks...", expanded=True) as status:
            monitor = PKIMonitor(str(artifacts_path), str(log_path))
            ok = monitor.run_all_checks()
            status.update(label="Checks completed" if ok else "Checks finished with issues", state="complete")

        st.subheader("Summary")
        render_summary(monitor)

        st.subheader("Session results")
        st.dataframe(monitor.results, use_container_width=True, hide_index=True)

    elif show_summary_only:
        monitor = PKIMonitor(str(artifacts_path), str(log_path))
        if log_path.exists():
            with open(log_path, "r", newline="") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    monitor.results.append(row)

            st.subheader("Summary")
            render_summary(monitor)
        else:
            st.warning("No log file found. Run checks first.")

    st.subheader("Latest log entries")
    rows = read_csv_as_dicts(log_path, None)
    if rows:
        st.dataframe(rows[-last_n:], use_container_width=True, hide_index=True)

        csv_buf = StringIO()
        writer = csv.DictWriter(csv_buf, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
        st.download_button(
            label="Download full CSV",
            data=csv_buf.getvalue(),
            file_name=Path(log_path).name,
            mime="text/csv",
        )
    else:
        st.info("No results yet. Run checks to generate the CSV log.")

    st.subheader("Downloaded Artifacts")
    artifact_files = list_artifacts(artifacts_path)
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


