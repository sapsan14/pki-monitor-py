"""
LDAP Checker Module

Handles LDAP/LDAPS connectivity and query testing for PKI services.
"""

import socket
import ssl
import time
from typing import Dict, List, Optional

from ldap3 import Server, Connection, Tls, LEVEL


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
                'sha256_or_note': '',
                'note': str(e)
            }
    
    def _check_ldap_query(self, protocol: str) -> Dict:
        """Check LDAP query via specified protocol (ldap/ldaps) using ldap3."""
        timestamp = self._timestamp()
        start_time = time.time()
        
        print(f"[{timestamp}] Checking LDAP query via {protocol}://{self.LDAP_HOST} ...")
        
        try:
            use_ssl = protocol == "ldaps"
            tls = None
            if use_ssl:
                # Mirror previous behavior for ldaps: do not require valid server cert
                tls = Tls(validate=ssl.CERT_NONE)
            server = Server(self.LDAP_HOST, use_ssl=use_ssl, connect_timeout=self.TIMEOUT, tls=tls)
            conn = Connection(server, auto_bind=True, receive_timeout=self.TIMEOUT)

            # one-level search (equivalent to ldapsearch -s one)
            success = conn.search(
                search_base=self.LDAP_BASE,
                search_filter=self.LDAP_FILTER,
                search_scope=LEVEL,
                attributes=["cn"],
                time_limit=self.TIMEOUT,
            )

            duration_ms = int((time.time() - start_time) * 1000)

            if success and conn.entries:
                first = str(conn.entries[0].entry_dn)
                print(f"[{timestamp}] ✅ Entry found: dn: {first}")
                note = 'found'
            elif success:
                print(f"[{timestamp}] ⚠️ Response received, but no entries found")
                note = 'empty'
            else:
                print(f"[{timestamp}] ❌ LDAP search returned no result (operation failed)")
                return {
                    'timestamp': timestamp,
                    'type': 'ldap_search',
                    'url_or_host': f"{protocol}://{self.LDAP_HOST}",
                    'status': 'fail',
                    'http_code_or_port': protocol.upper(),
                    'ms': str(duration_ms),
                    'sha256_or_note': '',
                    'note': 'operation failed'
                }

            return {
                'timestamp': timestamp,
                'type': 'ldap_search',
                'url_or_host': f"{protocol}://{self.LDAP_HOST}",
                'status': 'ok',
                'http_code_or_port': protocol.upper(),
                'ms': str(duration_ms),
                'sha256_or_note': '',
                'note': note
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
                'sha256_or_note': '',
                'note': str(e)
            }
    
    @staticmethod
    def _timestamp() -> str:
        """Get current UTC timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
