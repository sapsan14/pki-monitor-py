#!/usr/bin/env python3
"""
PKI Site Health Check - Python CLI Application

A Python command line application for checking the availability and correctness 
of public PKI services for ZETES / eID PKI (Estonia).

This replaces the original bash scripts with a unified Python implementation.
"""

import argparse
import csv
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from pki_checker import PKIChecker
from ocsp_checker import OCSPChecker
from ldap_checker import LDAPChecker


class PKIMonitor:
    """Main orchestrator class for PKI monitoring."""
    
    def __init__(self, artifacts_dir: str = "./artifacts", log_csv: str = "./results.csv"):
        self.artifacts_dir = Path(artifacts_dir)
        self.log_csv = Path(log_csv)
        self.results: List[Dict] = []
        
        # Initialize checkers
        self.pki_checker = PKIChecker(artifacts_dir, log_csv)
        self.ocsp_checker = OCSPChecker(artifacts_dir, log_csv)
        self.ldap_checker = LDAPChecker(log_csv)
        
        # Ensure directories exist
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)
        self._init_csv_log()
    
    def _init_csv_log(self):
        """Initialize CSV log file with headers if it doesn't exist."""
        if not self.log_csv.exists():
            with open(self.log_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    'timestamp', 'type', 'url_or_host', 'status', 
                    'http_code_or_port', 'ms', 'filepath_or_note', 
                    'sha256_or_note', 'note'
                ])
    
    def _log_result(self, result: Dict):
        """Log a result to CSV and internal results list."""
        self.results.append(result)
        
        with open(self.log_csv, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                result.get('timestamp', ''),
                result.get('type', ''),
                result.get('url_or_host', ''),
                result.get('status', ''),
                result.get('http_code_or_port', ''),
                result.get('ms', ''),
                result.get('filepath_or_note', ''),
                result.get('sha256_or_note', ''),
                result.get('note', '')
            ])
    
    def run_all_checks(self) -> bool:
        """Run all PKI checks and return success status."""
        print(f"[{self._timestamp()}] 🚀 Starting PKI checks...")
        
        success = True
        
        # Run PDF/CRT/CRL checks
        print("----------------------------------------")
        print(f"[{self._timestamp()}] ▶ Running PDF/CRT/CRL checks")
        print("----------------------------------------")
        try:
            pki_results = self.pki_checker.run_checks()
            for result in pki_results:
                self._log_result(result)
        except Exception as e:
            print(f"⚠️ PDF/CRT/CRL checks finished with an error: {e}")
            success = False
        
        # Run OCSP checks
        print("----------------------------------------")
        print(f"[{self._timestamp()}] ▶ Running OCSP checks")
        print("----------------------------------------")
        try:
            ocsp_results = self.ocsp_checker.run_checks()
            for result in ocsp_results:
                self._log_result(result)
        except Exception as e:
            print(f"⚠️ OCSP checks finished with an error: {e}")
            success = False
        
        # Run LDAP checks
        print("----------------------------------------")
        print(f"[{self._timestamp()}] ▶ Running LDAP checks")
        print("----------------------------------------")
        try:
            ldap_results = self.ldap_checker.run_checks()
            for result in ldap_results:
                self._log_result(result)
        except Exception as e:
            print(f"⚠️ LDAP checks finished with an error: {e}")
            success = False
        
        return success
    
    def print_summary(self):
        """Print summary of all results."""
        print()
        print(f"[{self._timestamp()}] 📊 Results summary:")
        print("----------------------------------------")
        
        # Count results by type
        pdf_results = [r for r in self.results if r.get('type', '').startswith('pdf_')]
        crt_results = [r for r in self.results if r.get('type', '').startswith('crt_')]
        crl_results = [r for r in self.results if r.get('type', '').startswith('crl_')]
        ocsp_results = [r for r in self.results if r.get('type', '').startswith('ocsp_')]
        ldap_search_results = [r for r in self.results if r.get('type') == 'ldap_search']
        ldap_port_results = [r for r in self.results if r.get('type') == 'ldap_port']
        
        # Count successful results
        pdf_ok = len([r for r in pdf_results if r.get('status') == 'ok'])
        crt_ok = len([r for r in crt_results if r.get('status') == 'ok'])
        crl_ok = len([r for r in crl_results if r.get('status') == 'ok'])
        ocsp_ok = len([r for r in ocsp_results if r.get('status') == 'ok'])
        ldap_search_ok = len([r for r in ldap_search_results if r.get('status') == 'ok'])
        ldap_port_ok = len([r for r in ldap_port_results if r.get('status') == 'ok'])
        
        print(f"📄 PDF:  {pdf_ok}/{len(pdf_results)} OK")
        print(f"🔏 CRT:  {crt_ok}/{len(crt_results)} OK")
        print(f"🚫 CRL:  {crl_ok}/{len(crl_results)} OK")
        print(f"🧩 OCSP: {ocsp_ok}/{len(ocsp_results)} OK")
        print(f"📡 LDAP: {ldap_search_ok} searches OK, {ldap_port_ok} ports OK")
        
        print("----------------------------------------")
        print(f"[{self._timestamp()}] ✅ Checks completed")
    
    def print_last_results(self, lines: int = 20):
        """Print last N lines of the CSV report."""
        print()
        print(f"[{self._timestamp()}] 📋 Last {lines} lines of the report:")
        print("----------------------------------------")
        
        if self.log_csv.exists():
            with open(self.log_csv, 'r') as f:
                all_lines = f.readlines()
                last_lines = all_lines[-lines:]
                for line in last_lines:
                    print(line.rstrip())
    
    @staticmethod
    def _timestamp() -> str:
        """Get current UTC timestamp in ISO format."""
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    """Main entry point for the PKI monitor CLI."""
    parser = argparse.ArgumentParser(
        description="PKI Site Health Check - Monitor ZETES / eID PKI services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python pki_monitor.py                    # Run all checks with default settings
  python pki_monitor.py --artifacts ./data # Use custom artifacts directory
  python pki_monitor.py --log results.log  # Use custom log file
  python pki_monitor.py --summary-only     # Show only summary without running checks
        """
    )
    
    parser.add_argument(
        '--artifacts', 
        default='./artifacts',
        help='Directory to store downloaded artifacts (default: ./artifacts)'
    )
    
    parser.add_argument(
        '--log', 
        default='./results.csv',
        help='CSV log file for results (default: ./results.csv)'
    )
    
    parser.add_argument(
        '--summary-only', 
        action='store_true',
        help='Show summary from existing log file without running new checks'
    )
    
    parser.add_argument(
        '--lines', 
        type=int, 
        default=20,
        help='Number of last lines to show from log (default: 20)'
    )
    
    args = parser.parse_args()
    
    # Initialize monitor
    monitor = PKIMonitor(args.artifacts, args.log)
    
    if args.summary_only:
        # Load existing results and show summary
        if monitor.log_csv.exists():
            with open(monitor.log_csv, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    monitor.results.append(row)
            monitor.print_summary()
            monitor.print_last_results(args.lines)
        else:
            print("❌ No log file found. Run checks first.")
            sys.exit(1)
    else:
        # Run all checks
        success = monitor.run_all_checks()
        monitor.print_summary()
        monitor.print_last_results(args.lines)
        
        if not success:
            sys.exit(1)


if __name__ == "__main__":
    main()
