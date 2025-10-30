#!/usr/bin/env python3
"""
Simple test script for PKI Monitor application.
This script tests the basic functionality without making actual network requests.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pki_monitor import PKIMonitor
from pki_checker import PKIChecker
from ocsp_checker import OCSPChecker
from ldap_checker import LDAPChecker


def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    try:
        import pki_monitor
        import pki_checker
        import ocsp_checker
        import ldap_checker
        print("✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_pki_monitor_initialization():
    """Test PKIMonitor initialization."""
    print("Testing PKIMonitor initialization...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            monitor = PKIMonitor(
                artifacts_dir=os.path.join(temp_dir, "artifacts"),
                log_csv=os.path.join(temp_dir, "test_results.csv")
            )
            print("✅ PKIMonitor initialized successfully")
            return True
    except Exception as e:
        print(f"❌ PKIMonitor initialization error: {e}")
        return False


def test_checker_initialization():
    """Test checker module initialization."""
    print("Testing checker initialization...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_dir = os.path.join(temp_dir, "artifacts")
            log_csv = os.path.join(temp_dir, "test_results.csv")
            
            pki_checker = PKIChecker(artifacts_dir, log_csv)
            ocsp_checker = OCSPChecker(artifacts_dir, log_csv)
            ldap_checker = LDAPChecker(log_csv)
            
            print("✅ All checkers initialized successfully")
            return True
    except Exception as e:
        print(f"❌ Checker initialization error: {e}")
        return False


def test_csv_log_creation():
    """Test CSV log file creation."""
    print("Testing CSV log creation...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            log_csv = os.path.join(temp_dir, "test_results.csv")
            monitor = PKIMonitor(
                artifacts_dir=os.path.join(temp_dir, "artifacts"),
                log_csv=log_csv
            )
            
            # Check if CSV file was created with proper headers
            if os.path.exists(log_csv):
                with open(log_csv, 'r') as f:
                    first_line = f.readline().strip()
                    expected_headers = "timestamp,type,url_or_host,status,http_code_or_port,ms,filepath_or_note,sha256_or_note,note"
                    if first_line == expected_headers:
                        print("✅ CSV log file created with correct headers")
                        return True
                    else:
                        print(f"❌ CSV headers mismatch. Expected: {expected_headers}, Got: {first_line}")
                        return False
            else:
                print("❌ CSV log file was not created")
                return False
    except Exception as e:
        print(f"❌ CSV log creation error: {e}")
        return False


def test_artifacts_directory_creation():
    """Test artifacts directory creation."""
    print("Testing artifacts directory creation...")
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            artifacts_dir = os.path.join(temp_dir, "artifacts")
            monitor = PKIMonitor(artifacts_dir=artifacts_dir, log_csv=os.path.join(temp_dir, "test.csv"))
            
            # Check if subdirectories were created
            subdirs = ["pdf", "crt", "crl"]
            for subdir in subdirs:
                subdir_path = os.path.join(artifacts_dir, subdir)
                if os.path.exists(subdir_path) and os.path.isdir(subdir_path):
                    print(f"✅ Created subdirectory: {subdir}")
                else:
                    print(f"❌ Failed to create subdirectory: {subdir}")
                    return False
            
            print("✅ All artifacts directories created successfully")
            return True
    except Exception as e:
        print(f"❌ Artifacts directory creation error: {e}")
        return False


def main():
    """Run all tests."""
    print("🧪 Running PKI Monitor tests...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_pki_monitor_initialization,
        test_checker_initialization,
        test_csv_log_creation,
        test_artifacts_directory_creation,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The PKI Monitor application is ready to use.")
        return 0
    else:
        print("❌ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
