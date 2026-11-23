#!/usr/bin/env python3
"""Create local Ed25519 signing keys without overwriting existing key material."""

from __future__ import annotations

import os
import sys

from nimbus_api.auth import generate_keypair
from nimbus_api.config import REPOSITORY_ROOT


def main() -> int:
    secrets_dir = REPOSITORY_ROOT / "secrets"
    private_path = secrets_dir / "jwt_ed25519.pem"
    public_path = secrets_dir / "jwt_ed25519.pub"
    if private_path.exists() or public_path.exists():
        print("Refusing to overwrite existing JWT key files.", file=sys.stderr)
        return 1

    secrets_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(secrets_dir, 0o700)
    private_pem, public_pem = generate_keypair()
    private_created = False
    try:
        with private_path.open("x", encoding="ascii") as private_file:
            private_file.write(private_pem)
            private_file.write("\n")
        private_created = True
        os.chmod(private_path, 0o600)
        with public_path.open("x", encoding="ascii") as public_file:
            public_file.write(public_pem)
            public_file.write("\n")
        os.chmod(public_path, 0o644)
    except FileExistsError:
        # A competing process may have created either key after the initial check.
        if private_created:
            private_path.unlink()
        print("A JWT key file appeared during generation; no overwrite performed.", file=sys.stderr)
        return 1

    print(f"Created Ed25519 keys in {secrets_dir} (private key mode 0600).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
