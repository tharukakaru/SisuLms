"""Local certificate check. No network, installation, writes or secret output."""
import argparse
import getpass
import warnings
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.serialization.pkcs12 import load_key_and_certificates
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('certificate')
    args = parser.parse_args()
    try:
        data = Path(args.certificate).read_bytes()
    except OSError:
        raise SystemExit('STOPPED: certificate file could not be read.') from None
    # Never fall back to an echoed password prompt.
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        try:
            password = getpass.getpass('P12 password (hidden): ')
        except getpass.GetPassWarning:
            raise SystemExit('STOPPED: run directly in an interactive terminal.') from None
    try:
        key, cert, _ = load_key_and_certificates(data, password.encode())
    except (ValueError, TypeError):
        raise SystemExit('STOPPED: could not unlock certificate; check file and password.') from None
    if not isinstance(key, RSAPrivateKey) or cert is None:
        raise SystemExit('STOPPED: RSA private key and certificate are required.')
    if key.public_key().public_numbers() != cert.public_key().public_numbers():
        raise SystemExit('STOPPED: private key does not match certificate.')
    start = cert.not_valid_before_utc
    end = cert.not_valid_after_utc
    if not start <= datetime.now(timezone.utc) < end:
        raise SystemExit('STOPPED: certificate is outside its validity period.')
    print('PASS: P12 unlocked; matching RSA private key and certificate present.')
    print('PASS: certificate within validity period; expires ' + end.date().isoformat() + ' UTC.')
    print('NOT TESTED: merchant/key-ID association, revocation or API authentication.')
    print('No network requests, payments, installation or file changes performed.')


if __name__ == '__main__':
    main()
