"""
LDAP Checker Module

Handles LDAP/LDAPS connectivity and query testing for PKI services.
"""

import os
import socket
import subprocess
import time
from typing import Dict, List, Optional


class LDAPChecker:
    """Handles LDAP/LDAPS connectivity and query testing."""
    
    LDAP_HOST = "ldap.eidpki.ee"
    LDAP_BASE = "dc=ldap,dc=eidpki,dc=ee"
    LDAP_FILTER = "(objectClass=*)"
    TIMEOUT = 10
    
    def __init__(self, log_csv: str):
        self.log_csv = log_csv
    
    def run_checks(self) -> List[Dict]:
        """Run all LDAP checks and return results."""
        results = []
        
        # Check LDAP ports
        results.append(self._check_port(self.LDAP_HOST, 389))  # LDAP
        results.append(self._check_port(self.LDAP_HOST, 636))  # LDAPS
        
        # Check LDAP queries
        results.append(self._check_ldap_query("ldap"))
        results.append(self._check_ldap_query("ldaps"))
        
        return results
    
    def _check_port(self, host: str, port: int) -> Dict:
        """Check if a port is open on the host."""
        timestamp = self._timestamp()
        start_time = time.time()
        
        print(f"[{timestamp}] Checking port {port} on {host}")
        
        try:
            # Create socket and set timeout
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.TIMEOUT)
            
            # Try to connect
            result = sock.connect_ex((host, port))
            sock.close()
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if result == 0:
                print(f"[{timestamp}] ✅ Port {port} is open ({duration_ms}ms)")
                status = 'ok'
            else:
                print(f"[{timestamp}] ❌ Port {port} is closed")
                status = 'fail'
                duration_ms = 0
            
            return {
                'timestamp': timestamp,
                'type': 'ldap_port',
                'url_or_host': host,
                'status': status,
                'http_code_or_port': str(port),
                'ms': str(duration_ms),
                'filepath_or_note': '',
                'sha256_or_note': '',
                'note': ''
            }
        
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"[{timestamp}] ❌ Port {port} check error: {e}")
            
            return {
                'timestamp': timestamp,
                'type': 'ldap_port',
                'url_or_host': host,
                'status': 'fail',
                'http_code_or_port': str(port),
                'ms': str(duration_ms),
                'filepath_or_note': '',
                'sha256_or_note': '',
                'note': str(e)
            }
    
    def _check_ldap_query(self, protocol: str) -> Dict:
        """Check LDAP query via specified protocol (ldap/ldaps)."""
        timestamp = self._timestamp()
        start_time = time.time()
        
        print(f"[{timestamp}] Checking LDAP query via {protocol}://{self.LDAP_HOST} ...")
        
        try:
            # Prepare environment for LDAP search
            env = os.environ.copy()
            if protocol == "ldaps":
                # Disable certificate verification for LDAPS
                env['LDAPTLS_REQCERT'] = 'never'
            
            # Build ldapsearch command
            url = f"{protocol}://{self.LDAP_HOST}"
            cmd = [
                'ldapsearch',
                '-x',  # Simple bind
                '-H', url,
                '-b', self.LDAP_BASE,
                '-s', 'one',  # Search scope
                self.LDAP_FILTER,
                'cn'  # Return only cn attribute
            ]
            
            # Run ldapsearch command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT,
                env=env
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            if result.returncode == 0:
                # Check if we got valid LDAP entries
                output_lines = result.stdout.split('\n')
                dn_lines = [line for line in output_lines if line.startswith('dn:')]
                
                if dn_lines:
                    dn_line = dn_lines[0]
                    print(f"[{timestamp}] ✅ Entry found: {dn_line}")
                    note = 'found'
                else:
                    print(f"[{timestamp}] ⚠️ Response received, but no entries found")
                    note = 'empty'
                
                return {
                    'timestamp': timestamp,
                    'type': 'ldap_search',
                    'url_or_host': url,
                    'status': 'ok',
                    'http_code_or_port': protocol.upper(),
                    'ms': str(duration_ms),
                    'filepath_or_note': '',
                    'sha256_or_note': '',
                    'note': note
                }
            else:
                print(f"[{timestamp}] ❌ ldapsearch error: {result.stderr}")
                return {
                    'timestamp': timestamp,
                    'type': 'ldap_search',
                    'url_or_host': f"{protocol}://{self.LDAP_HOST}",
                    'status': 'fail',
                    'http_code_or_port': protocol.upper(),
                    'ms': str(duration_ms),
                    'filepath_or_note': '',
                    'sha256_or_note': '',
                    'note': f'ldapsearch error: {result.stderr}'
                }
        
        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"[{timestamp}] ❌ LDAP query timeout")
            return {
                'timestamp': timestamp,
                'type': 'ldap_search',
                'url_or_host': f"{protocol}://{self.LDAP_HOST}",
                'status': 'fail',
                'http_code_or_port': protocol.upper(),
                'ms': str(duration_ms),
                'filepath_or_note': '',
                'sha256_or_note': '',
                'note': 'Query timeout'
            }
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"[{timestamp}] ❌ LDAP query error: {e}")
            return {
                'timestamp': timestamp,
                'type': 'ldap_search',
                'url_or_host': f"{protocol}://{self.LDAP_HOST}",
                'status': 'fail',
                'http_code_or_port': protocol.upper(),
                'ms': str(duration_ms),
                'filepath_or_note': '',
                'sha256_or_note': '',
                'note': str(e)
            }
    
    @staticmethod
    def _timestamp() -> str:
        """Get current UTC timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
