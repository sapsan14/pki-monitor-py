#!/usr/bin/env python3
"""
Example usage of PKI Monitor Python application.
This demonstrates how to use the PKI Monitor programmatically.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pki_monitor import PKIMonitor


def example_basic_usage():
    """Example of basic PKI monitoring usage."""
    print("🔍 Example: Basic PKI Monitoring")
    print("=" * 40)
    
    # Create a temporary directory for this example
    with tempfile.TemporaryDirectory() as temp_dir:
        artifacts_dir = os.path.join(temp_dir, "artifacts")
        log_csv = os.path.join(temp_dir, "results.csv")
        
        # Initialize the monitor
        monitor = PKIMonitor(artifacts_dir=artifacts_dir, log_csv=log_csv)
        
        print(f"Artifacts directory: {artifacts_dir}")
        print(f"Log file: {log_csv}")
        print()
        
        # Note: In a real scenario, you would run:
        # success = monitor.run_all_checks()
        # monitor.print_summary()
        # monitor.print_last_results()
        
        print("To run actual checks, use:")
        print("  success = monitor.run_all_checks()")
        print("  monitor.print_summary()")
        print("  monitor.print_last_results()")
        print()


def example_custom_settings():
    """Example of using custom settings."""
    print("🔧 Example: Custom Settings")
    print("=" * 40)
    
    # Example with custom directories
    custom_artifacts = "./my_pki_data"
    custom_log = "./my_results.csv"
    
    print(f"Custom artifacts directory: {custom_artifacts}")
    print(f"Custom log file: {custom_log}")
    print()
    
    # Initialize with custom settings
    monitor = PKIMonitor(artifacts_dir=custom_artifacts, log_csv=custom_log)
    
    print("Monitor initialized with custom settings.")
    print("Directories will be created automatically when needed.")
    print()


def example_programmatic_usage():
    """Example of programmatic usage for integration."""
    print("🔌 Example: Programmatic Integration")
    print("=" * 40)
    
    class PKIServiceMonitor:
        """Example service class that uses PKI Monitor."""
        
        def __init__(self, config_dir="./config"):
            self.config_dir = Path(config_dir)
            self.artifacts_dir = self.config_dir / "artifacts"
            self.log_file = self.config_dir / "pki_results.csv"
            
            # Initialize PKI Monitor
            self.monitor = PKIMonitor(
                artifacts_dir=str(self.artifacts_dir),
                log_csv=str(self.log_file)
            )
        
        def check_pki_health(self):
            """Check PKI health and return status."""
            print("Running PKI health checks...")
            
            # Run all checks
            success = self.monitor.run_all_checks()
            
            # Get summary
            self.monitor.print_summary()
            
            return success
        
        def get_last_results(self, lines=10):
            """Get last N results from log."""
            self.monitor.print_last_results(lines)
    
    # Example usage
    service = PKIServiceMonitor()
    print("PKI Service Monitor initialized.")
    print("To check health: service.check_pki_health()")
    print("To get results: service.get_last_results(10)")
    print()


def main():
    """Run all examples."""
    print("📚 PKI Monitor Python - Usage Examples")
    print("=" * 50)
    print()
    
    example_basic_usage()
    example_custom_settings()
    example_programmatic_usage()
    
    print("🚀 Command Line Usage Examples:")
    print("=" * 40)
    print("# Basic usage")
    print("python3 pki_monitor.py")
    print()
    print("# Custom directories")
    print("python3 pki_monitor.py --artifacts ./data --log ./results.csv")
    print()
    print("# Show summary only (no new checks)")
    print("python3 pki_monitor.py --summary-only")
    print()
    print("# Show more log lines")
    print("python3 pki_monitor.py --lines 50")
    print()
    print("# Get help")
    print("python3 pki_monitor.py --help")
    print()
    print("✅ Examples completed!")


if __name__ == "__main__":
    main()
