"""Verified HTTPS trust for system and privately managed desktop Python."""
from functools import lru_cache
from pathlib import Path
import platform
import ssl
import subprocess


@lru_cache(maxsize=1)
def tls_context():
    # Windows roots are loaded by create_default_context. Supplement OpenSSL
    # defaults with Linux distribution bundles and macOS system Keychains.
    context = ssl.create_default_context()
    for filename in (
        '/etc/ssl/certs/ca-certificates.crt', '/etc/ssl/cert.pem',
        '/etc/pki/tls/certs/ca-bundle.crt',
        '/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem',
    ):
        if Path(filename).is_file():
            try:
                context.load_verify_locations(cafile=filename)
            except (OSError, ssl.SSLError):
                # A stale optional bundle must not discard valid default roots.
                pass
    if platform.system() == 'Darwin':
        for keychain in (
            '/System/Library/Keychains/SystemRootCertificates.keychain',
            '/Library/Keychains/System.keychain',
        ):
            try:
                result = subprocess.run(
                    ['/usr/bin/security', 'find-certificate', '-a', '-p', keychain],
                    capture_output=True, text=True, timeout=15,
                )
                if result.returncode == 0 and result.stdout.strip():
                    context.load_verify_locations(cadata=result.stdout)
            except (OSError, subprocess.TimeoutExpired, ssl.SSLError):
                pass
    # Never disable verification when the machine has no usable trust roots.
    return context
