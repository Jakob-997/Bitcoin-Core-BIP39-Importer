#!/usr/bin/env python3
import getpass
import hashlib
import hmac
import json
import subprocess
import sys

from mnemonic import Mnemonic

BASE58 = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
ORDER = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
WALLET = "bip39-import"
TYPES = ("legacy", "p2sh-segwit", "bech32", "bech32m")


def fail(msg):
    raise SystemExit(f"Error: {msg}")


def rpc(cli, args, wallet=None, secret=None):
    cmd = [cli]
    if wallet:
        cmd.append(f"-rpcwallet={wallet}")
    if secret is not None:
        cmd.append("-stdin")
    cmd += args
    p = subprocess.run(
        cmd,
        input=None if secret is None else secret + "\n",
        text=True,
        capture_output=True,
    )
    if p.returncode:
        fail(p.stderr.strip() or p.stdout.strip())
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        return p.stdout.strip()


def base58check(payload):
    data = payload + hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
    zeros = len(data) - len(data.lstrip(b"\0"))
    n = int.from_bytes(data, "big")
    out = bytearray()
    while n:
        n, r = divmod(n, 58)
        out.append(BASE58[r])
    return (BASE58[:1] * zeros + bytes(reversed(out))).decode()


def master_xprv(seed, testnet=False):
    digest = hmac.new(b"Bitcoin seed", seed, hashlib.sha512).digest()
    key, chain = digest[:32], digest[32:]
    if not 0 < int.from_bytes(key, "big") < ORDER:
        fail("Invalid BIP32 master key.")
    version = bytes.fromhex("04358394" if testnet else "0488ade4")
    return base58check(version + b"\0" * 9 + chain + b"\0" + key)


def main():
    if len(sys.argv) not in (2, 3):
        fail("Usage: tails.sh [--bip39-passphrase]")
    if len(sys.argv) == 3 and sys.argv[2] != "--bip39-passphrase":
        fail("Only supported option: --bip39-passphrase")

    cli = sys.argv[1]
    bip39 = Mnemonic("english")

    words = input("BIP39 mnemonic: ").strip()
    if not bip39.check(words):
        fail("Invalid BIP39 mnemonic.")

    passphrase = (
        getpass.getpass("BIP39 passphrase: ")
        if len(sys.argv) == 3
        else ""
    )
    seed = bip39.to_seed(words, passphrase)

    chain = rpc(cli, ["getblockchaininfo"])["chain"]
    xprv = master_xprv(seed, chain != "main")

    rpc(cli, ["createwallet", WALLET, "false", "true"])
    added = rpc(cli, ["addhdkey"], wallet=WALLET, secret=xprv)
    xpub = added["xpub"]

    for address_type in TYPES:
        rpc(
            cli,
            ["createwalletdescriptor", address_type, json.dumps({"hdkey": xpub})],
            wallet=WALLET,
        )

    print(f"Imported BIP39 wallet into Bitcoin Core wallet: {WALLET}")


if __name__ == "__main__":
    main()
