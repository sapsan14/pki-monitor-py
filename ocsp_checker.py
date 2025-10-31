"""
OCSP Checker Module

Handles Online Certificate Status Protocol (OCSP) checks for certificate validation.
"""

import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


class OCSPChecker:
    """Handles OCSP endpoint checking and certificate status validation."""
    
    OCSP_URLS = [
        "https://ocsp.eidpki.ee"
    ]
    
    def __init__(self, artifacts_dir: str, log_csv: str):
        self.artifacts_dir = Path(artifacts_dir)
        self.log_csv = log_csv
        self.timeout = 15
        self.connect_timeout = 5
        
        # Expected certificate files
        self.ca_cert = self.artifacts_dir / "crt" / "ESTEID2025.crt"
    
    def run_checks(self) -> List[Dict]:
        """Run all OCSP checks and return results."""
        results = []
        
        for url in self.OCSP_URLS:
            # Check OCSP HTTP availability
            results.append(self._check_ocsp_http(url))
            
            # Check OCSP certificate status
            results.append(self._check_ocsp_status(url))
        
        return results
    
    def _check_ocsp_http(self, url: str) -> Dict:
        """Check if OCSP endpoint is accessible via HTTP."""
        timestamp = self._timestamp()
        start_time = time.time()
        
        print(f"[{timestamp}] Checking OCSP availability: {url}")
        
        try:
            # Primary attempt: HEAD request with explicit headers
            headers = {
                'User-Agent': 'curl/8.7.1',
                'Accept': '*/*',
                'Connection': 'close',
            }
            head_request = Request(url, headers=headers)
            head_request.get_method = lambda: 'HEAD'
            
            try:
                with urlopen(head_request, timeout=self.connect_timeout) as response:
                    http_code = response.getcode()
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    status = 'ok' if http_code in [200, 206] else 'fail'
                    print(f"[{timestamp}] ✅ OCSP HTTP: {http_code} ({duration_ms}ms)")
                    
                    return {
                        'timestamp': timestamp,
                        'type': 'ocsp_http_check',
                        'url_or_host': url,
                        'status': status,
                        'http_code_or_port': str(http_code),
                        'ms': str(duration_ms),
                        'sha256_or_note': '',
                        'note': ''
                    }
            except HTTPError as e:
                # Some servers block HEAD; fallback to GET with Range 0-0
                if e.code in (403, 405):
                    pass
                else:
                    raise
            
            # Fallback attempt: GET first byte to verify availability
            range_headers = {
                'User-Agent': 'curl/8.7.1',
                'Accept': '*/*',
                'Connection': 'close',
                'Range': 'bytes=0-0',
            }
            get_request = Request(url, headers=range_headers)
            with urlopen(get_request, timeout=self.connect_timeout) as response:
                http_code = response.getcode()
                duration_ms = int((time.time() - start_time) * 1000)
                status = 'ok' if http_code in [200, 206] else 'fail'
                print(f"[{timestamp}] ✅ OCSP HTTP: {http_code} ({duration_ms}ms)")
                return {
                    'timestamp': timestamp,
                    'type': 'ocsp_http_check',
                    'url_or_host': url,
                    'status': status,
                    'http_code_or_port': str(http_code),
                    'ms': str(duration_ms),
                    'sha256_or_note': '',
                    'note': ''
                }
        
        except (URLError, HTTPError, OSError) as e:
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"[{timestamp}] ❌ OCSP HTTP error: {e}")
            
            return {
                'timestamp': timestamp,
                'type': 'ocsp_http_check',
                'url_or_host': url,
                'status': 'fail',
                'http_code_or_port': '000',
                'ms': str(duration_ms),
                'sha256_or_note': '',
                'note': str(e)
            }
    
    def _check_ocsp_status(self, url: str) -> Dict:
        """Check certificate status via OCSP using serial number instead of certificate file."""
        timestamp = self._timestamp()
        
        print(f"[{timestamp}] Checking certificate OCSP status via {url}")
        
        # Check if CA certificate exists (needed for issuer)
        if not self.ca_cert.exists():
            print(f"[{timestamp}] ❌ CA certificate not found: {self.ca_cert}")
            return {
                'timestamp': timestamp,
                'type': 'ocsp_status',
                'url_or_host': url,
                'status': 'fail',
                'http_code_or_port': '000',
                'ms': '0',
                'sha256_or_note': '',
                'note': f'CA certificate not found: {self.ca_cert}'
            }
        
        # Use a known test serial number for OCSP checks
        # This avoids needing the actual certificate file
        test_serial = '0xAAA'
        
        # Use the existing check_ocsp_by_serial method
        return self.check_ocsp_by_serial(url, str(self.ca_cert), test_serial, result_type='ocsp_status')
    
    def check_ocsp_by_serial(self, url: str, issuer_cert: str, serial: str, result_type: str = 'ocsp_status_by_serial') -> Dict:
        """Check certificate status via OCSP using serial number."""
        timestamp = self._timestamp()
        start_time = time.time()
        
        print(f"[{timestamp}] Checking OCSP status for serial {serial} via {url}")
        
        # Check if issuer certificate exists
        issuer_path = Path(issuer_cert)
        if not issuer_path.exists():
            print(f"[{timestamp}] ❌ Issuer certificate not found: {issuer_cert}")
            duration_ms = int((time.time() - start_time) * 1000)
            return {
                'timestamp': timestamp,
                'type': result_type,
                'url_or_host': url,
                'status': 'fail',
                'http_code_or_port': '000',
                'ms': str(duration_ms),
                'sha256_or_note': '',
                'note': f'Issuer certificate not found: {issuer_cert}'
            }
        
        # Run OpenSSL OCSP command with serial number
        try:
            with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as tmp_file:
                tmp_path = tmp_file.name
            
            # Extract hostname from URL for Host header
            parsed_url = urlparse(url)
            hostname = parsed_url.hostname
            
            # Build OpenSSL OCSP command with serial number
            cmd = [
                'openssl', 'ocsp',
                '-url', url,
                '-issuer', str(issuer_path),
                '-serial', serial,
                '-resp_text',
                '-noverify',
                '-timeout', '10'
            ]
            
            # Run the command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Write output to temp file for analysis
            with open(tmp_path, 'w') as f:
                f.write(result.stdout)
                f.write(result.stderr)
            
            if result.returncode == 0:
                # Parse OCSP response
                status = self._parse_ocsp_response(result.stdout)
                sha256_hash = self._calculate_file_sha256(tmp_path)
                
                print(f"[{timestamp}] ✅ OCSP response for serial {serial}: {status}")
                
                return {
                    'timestamp': timestamp,
                    'type': result_type,
                    'url_or_host': url,
                    'status': 'ok',
                    'http_code_or_port': '200',
                    'ms': str(duration_ms),
                    'sha256_or_note': sha256_hash,
                    'note': f"{status} (serial: {serial})"
                }
            else:
                print(f"[{timestamp}] ❌ OCSP request error for serial {serial}: {result.stderr}")
                return {
                    'timestamp': timestamp,
                    'type': result_type,
                    'url_or_host': url,
                    'status': 'fail',
                    'http_code_or_port': '000',
                    'ms': str(duration_ms),
                    'sha256_or_note': '',
                    'note': f'OpenSSL error: {result.stderr}'
                }
        
        except subprocess.TimeoutExpired:
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"[{timestamp}] ❌ OCSP request timeout for serial {serial}")
            return {
                'timestamp': timestamp,
                'type': result_type,
                'url_or_host': url,
                'status': 'fail',
                'http_code_or_port': '000',
                'ms': str(duration_ms),
                'sha256_or_note': '',
                'note': 'Request timeout'
            }
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"[{timestamp}] ❌ OCSP request error for serial {serial}: {e}")
            return {
                'timestamp': timestamp,
                'type': result_type,
                'url_or_host': url,
                'status': 'fail',
                'http_code_or_port': '000',
                'ms': str(duration_ms),
                'sha256_or_note': '',
                'note': str(e)
            }
        finally:
            # Clean up temp file
            if 'tmp_path' in locals() and os.path.exists(tmp_path):
                try:
                    os.unlink(tmp_path)
                except OSError:
                    pass
    
    def _parse_ocsp_response(self, response: str) -> str:
        """Parse OCSP response to extract certificate status and revocation info."""
        lines = response.split('\n')
        
        status = None
        revocation_time = None
        revocation_reason = None
        
        for line in lines:
            if 'Cert Status:' in line:
                # Extract status after the colon
                status = line.split('Cert Status:')[1].strip()
            elif 'Revocation Time:' in line:
                # Extract revocation time
                revocation_time = line.split('Revocation Time:')[1].strip()
            elif 'Revocation Reason:' in line:
                # Extract revocation reason
                revocation_reason = line.split('Revocation Reason:')[1].strip()
        
        if status is None:
            return 'unknown'
        
        # Format the response with revocation info if available
        if revocation_time:
            result = f"{status}, Revocation Time: {revocation_time}"
            if revocation_reason:
                result += f", Reason: {revocation_reason}"
            return result
        
        return status
    
    def _calculate_file_sha256(self, filepath: str) -> str:
        """Calculate SHA256 hash of a file."""
        import hashlib
        sha256_hash = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def _timestamp() -> str:
        """Get current UTC timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
