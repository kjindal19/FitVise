"""Generate a VAPID keypair for Web Push.

    docker compose run --rm backend python -m app.notifications.vapid_gen

Paste the printed values into .env as FITVISE_VAPID_PUBLIC_KEY /
FITVISE_VAPID_PRIVATE_KEY, then restart the stack.
"""
from __future__ import annotations

import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def generate() -> tuple[str, str]:
    key = ec.generate_private_key(ec.SECP256R1())

    private_bytes = key.private_numbers().private_value.to_bytes(32, "big")
    public = key.public_key().public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    )
    return _b64(public), _b64(private_bytes)


def main() -> None:
    public_key, private_key = generate()
    print("FITVISE_VAPID_PUBLIC_KEY=" + public_key)
    print("FITVISE_VAPID_PRIVATE_KEY=" + private_key)


if __name__ == "__main__":
    main()
