"""
PKI Checker Module

Handles downloading and checking PDF documents, certificates (CRT), 
and Certificate Revocation Lists (CRL) from PKI repositories.
"""

import hashlib
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError


class PKIChecker:
    """Handles PDF, CRT, and CRL download and validation."""
    
    # PDF documents to check
    PDF_URLS = [
        "https://repository.eidpki.ee/static/Root%20CP_V%201.1%20-%20signed%2030.05.2025.pdf",
        "https://repository.eidpki.ee/static/Root%20CP_V%201.1%20-%20signed%2030.05.2025.pdf",
        "https://repository.eidpki.ee/static/2025%2010%2003%20-%20ZE%20CPS-ID1-ROOT-CA%20v1.3%20-%20Approved.pdf",
        "https://repository.eidpki.ee/static/2025%2010%2001%20-%20ZE%20CPS-ID1-EID-CA%20v1.3%20-%20Approved.pdf",
        "https://repository.eidpki.ee/static/2025%2010%2003%20-%20ZE%20TSPS-ID1%20v1.3%20-%20Approved.pdf",
        "https://repository.eidpki.ee/static/2025%2010%2003%20-%20ZE%20TC-ID1%20v1.3%20-%20Approved.pdf",
        "https://repository.eidpki.ee/static/2025%2010%2003%20-%20ZE%20TC-ID1-SUB%20v1.3%20-%20Approved.pdf",
        "https://repository.eidpki.ee/static/2025-10-03-ze-tc-id1-sub-v1.3_PBGB_Estonian%20Approved.pdf",
        "https://repository.eidpki.ee/static/Technical%20profile%20of%20certificates%20OCSP%20responses%20and%20CRLs_20251001_withoutUAT.pdf",
    ]
    
    # Certificates to check
    CRT_URLS = [
        "https://crt.eidpki.ee/EEGovCA2025.crt",
        "https://crt.eidpki.ee/ESTEID2025.crt",
    ]
    
    # CRL files to check
    CRL_URLS = [
        "https://crl.eidpki.ee/EEGovCA2025.crl",
        "https://crl.eidpki.ee/ESTEID2025.crl",
    ]
    
    def __init__(self, artifacts_dir: str, log_csv: str):
        self.artifacts_dir = Path(artifacts_dir)
        self.log_csv = log_csv
        self.timeout = 60
        self.connect_timeout = 10
        
        # Create subdirectories
        (self.artifacts_dir / "pdf").mkdir(parents=True, exist_ok=True)
        (self.artifacts_dir / "crt").mkdir(parents=True, exist_ok=True)
        (self.artifacts_dir / "crl").mkdir(parents=True, exist_ok=True)
    
    def run_checks(self) -> List[Dict]:
        """Run all PKI checks and return results."""
        results = []
        
        # Check PDF documents
        for url in self.PDF_URLS:
            results.extend(self._download_file(url, "pdf", self.artifacts_dir / "pdf"))
        
        # Check certificates
        for url in self.CRT_URLS:
            results.extend(self._download_file(url, "crt", self.artifacts_dir / "crt"))
        
        # Check CRL files
        for url in self.CRL_URLS:
            results.extend(self._download_file(url, "crl", self.artifacts_dir / "crl"))
        
        return results
    
    def _download_file(self, url: str, file_type: str, output_dir: Path) -> List[Dict]:
        """Download a file and return check results."""
        results = []
        timestamp = self._timestamp()
        
        print(f"[{timestamp}] Checking [{file_type}]: {url}")
        
        # First, check if URL is accessible (HEAD request)
        check_result = self._check_url_accessibility(url, file_type)
        results.append(check_result)
        
        # If accessible, download the file
        if check_result['status'] == 'ok':
            download_result = self._download_full_file(url, file_type, output_dir)
            results.append(download_result)
        else:
            # Log failed download attempt
            results.append({
                'timestamp': timestamp,
                'type': f'{file_type}_download',
                'url_or_host': url,
                'status': 'fail',
                'http_code_or_port': '000',
                'ms': '0',
                'sha256_or_note': '',
                'note': 'URL not accessible'
            })
        
        return results
    
    def _check_url_accessibility(self, url: str, file_type: str) -> Dict:
        """Check if URL is accessible via HEAD request."""
        timestamp = self._timestamp()
        start_time = time.time()
        
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
                    content_type = response.headers.get('Content-Type', 'unknown')
                    duration_ms = int((time.time() - start_time) * 1000)
                    
                    status = 'ok' if http_code in [200, 206] else 'fail'
                    
                    print(f"[{timestamp}] ✅ {file_type} accessible: HTTP {http_code} ({duration_ms}ms)")
                    
                    return {
                        'timestamp': timestamp,
                        'type': f'{file_type}_check',
                        'url_or_host': url,
                        'status': status,
                        'http_code_or_port': str(http_code),
                        'ms': str(duration_ms),
                        'sha256_or_note': '',
                        'note': f'Content-Type: {content_type}'
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
                content_type = response.headers.get('Content-Type', 'unknown')
                duration_ms = int((time.time() - start_time) * 1000)
                # 206 (Partial Content) or 200 are acceptable
                status = 'ok' if http_code in [200, 206] else 'fail'
                print(f"[{timestamp}] ✅ {file_type} accessible: HTTP {http_code} ({duration_ms}ms)")
                return {
                    'timestamp': timestamp,
                    'type': f'{file_type}_check',
                    'url_or_host': url,
                    'status': status,
                    'http_code_or_port': str(http_code),
                    'ms': str(duration_ms),
                    'sha256_or_note': '',
                    'note': f'Content-Type: {content_type}'
                }
        
        except (URLError, HTTPError, OSError) as e:
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"[{timestamp}] ❌ {file_type} not accessible: {e}")
            
            return {
                'timestamp': timestamp,
                'type': f'{file_type}_check',
                'url_or_host': url,
                'status': 'fail',
                'http_code_or_port': '000',
                'ms': str(duration_ms),
                'sha256_or_note': '',
                'note': str(e)
            }
    
    def _download_full_file(self, url: str, file_type: str, output_dir: Path) -> Dict:
        """Download the full file and calculate SHA256 hash."""
        timestamp = self._timestamp()
        start_time = time.time()
        
        try:
            # Generate filename with timestamp
            parsed_url = urlparse(url)
            base_name = os.path.basename(parsed_url.path)
            if not base_name:
                base_name = f"{file_type}_file"
            
            timestamp_str = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
            filename = f"{timestamp_str}-{base_name}"
            filepath = output_dir / filename
            
            # Download file (provide explicit headers like a common client)
            dl_headers = {
                'User-Agent': 'curl/8.7.1',
                'Accept': '*/*',
                'Connection': 'close',
            }
            dl_request = Request(url, headers=dl_headers)
            with urlopen(dl_request, timeout=self.timeout) as response:
                with open(filepath, 'wb') as f:
                    f.write(response.read())
            
            # Calculate SHA256 hash
            sha256_hash = self._calculate_sha256(filepath)
            duration_ms = int((time.time() - start_time) * 1000)
            
            print(f"[{timestamp}] ✅ {file_type} saved: {filepath} (sha256={sha256_hash})")
            
            return {
                'timestamp': timestamp,
                'type': f'{file_type}_download',
                'url_or_host': url,
                'status': 'ok',
                'http_code_or_port': '200',
                'ms': str(duration_ms),
                'sha256_or_note': sha256_hash,
                'note': ''
            }
        
        except (URLError, HTTPError, OSError) as e:
            duration_ms = int((time.time() - start_time) * 1000)
            print(f"[{timestamp}] ❌ Download error for {file_type}: {e}")
            
            return {
                'timestamp': timestamp,
                'type': f'{file_type}_download',
                'url_or_host': url,
                'status': 'fail',
                'http_code_or_port': '000',
                'ms': str(duration_ms),
                'sha256_or_note': '',
                'note': str(e)
            }
    
    def _calculate_sha256(self, filepath: Path) -> str:
        """Calculate SHA256 hash of a file."""
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
