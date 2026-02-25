#!/usr/bin/env python3
"""
Utility: generate Ed25519 keypair for Robinhood trading API and save files.

Usage:
  python3 generate_robinhood_keys.py --api-key YOUR_API_KEY

This script will:
  - create an Ed25519 signing key (32-byte seed)
  - save the base64-encoded private seed to `r_secret.txt`
  - optionally save the provided API key to `r_key.txt`
  - print the public key (base64, hex, and PEM) so you can paste it into Robinhood's
    developer/API key setup page.

Security: Keep `r_secret.txt` private. Do not commit it to source control.
"""
import base64
import argparse
import os
from nacl.signing import SigningKey


def make_dir_for_file(path: str) -> None:
    d = os.path.dirname(path) or "."
    os.makedirs(d, exist_ok=True)


def generate_keys(api_key: str | None = None, out_secret: str = "r_secret.txt", out_key: str = "r_key.txt") -> None:
    # Generate a new SigningKey (Ed25519)
    sk = SigningKey.generate()
    seed = sk.encode()  # 32 bytes
    vk = sk.verify_key
    pub = vk.encode()

    b64_seed = base64.b64encode(seed).decode("utf-8")
    b64_pub = base64.b64encode(pub).decode("utf-8")

    # PEM-style public key (RFC 8410-like minimal wrapper)
    pem_pub = (
        "-----BEGIN PUBLIC KEY-----\n"
        + "".join([b64_pub[i:i+64] + "\n" for i in range(0, len(b64_pub), 64)])
        + "-----END PUBLIC KEY-----\n"
    )

    # Save private seed (base64) to out_secret
    make_dir_for_file(out_secret)
    with open(out_secret, "w", encoding="utf-8") as f:
        f.write(b64_seed)

    # If API key provided, save it
    if api_key:
        make_dir_for_file(out_key)
        with open(out_key, "w", encoding="utf-8") as f:
            f.write(api_key.strip())

    print("\nKeys generated and private seed saved to:")
    print(f"  {out_secret}")
    if api_key:
        print(f"  {out_key} (saved)")
    else:
        print(f"  {out_key} (not written, run with --api-key to save it)")

    print("\nPublic key formats (paste the public key into Robinhood's UI where requested):\n")
    print("Base64 public key:")
    print(b64_pub)
    print("\nHex public key:")
    print(pub.hex())
    print("\nPEM-style public key:\n")
    print(pem_pub)


def main():
    p = argparse.ArgumentParser(description="Generate Robinhood Ed25519 keypair and save seed + API key.")
    p.add_argument("--api-key", dest="api_key", help="Robinhood API key (will be saved to r_key.txt)")
    p.add_argument("--secret-path", dest="secret_path", default="r_secret.txt", help="Path to save the base64 private seed")
    p.add_argument("--key-path", dest="key_path", default="r_key.txt", help="Path to save the API key (optional)")
    args = p.parse_args()

    if os.path.exists(args.secret_path):
        resp = input(f"{args.secret_path} already exists. Overwrite? [y/N]: ").strip().lower()
        if resp not in ("y", "yes"):
            print("Aborting: not overwriting existing secret file.")
            return

    generate_keys(api_key=args.api_key, out_secret=args.secret_path, out_key=args.key_path)


if __name__ == "__main__":
    main()
