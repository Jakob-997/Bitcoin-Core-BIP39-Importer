#!/usr/bin/env python3
import getpass
import hashlib
import hmac
import json
from pathlib import Path
import subprocess
import sys
import unicodedata

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


def mnemonic(raw):
    words = unicodedata.normalize("NFKD", raw.strip()).split()
    if len(words) not in (12, 15, 18, 21, 24):
        fail("BIP39 mnemonic must contain 12, 15, 18, 21, or 24 words.")

    wordlist = Path(__file__).with_name("bip39_english.txt").read_text().splitlines()
    positions = {word: i for i, word in enumerate(wordlist)}
    try:
        bits = "".join(f"{positions[word]:011b}" for word in words)
    except KeyError as e:
        fail(f"Not a BIP39 English word: {e.args[0]}")

    ent = len(bits) * 32 // 33
    entropy = int(bits[:ent], 2).to_bytes(ent // 8, "big")
    checksum = f"{int.from_bytes(hashlib.sha256(entropy).digest(), 'big'):0256b}"
    if bits[ent:] != checksum[: len(bits) - ent]:
        fail("Invalid BIP39 checksum.")
    return " ".join(words)


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
    if len(sys.argv) != 2:
        fail("Run through tails.sh.")

    cli = sys.argv[1]
    phrase = mnemonic(input("BIP39 mnemonic: "))
    bip39_pass = getpass.getpass("BIP39 passphrase (blank if none): ")
    wallet_pass = getpass.getpass("Core wallet passphrase (blank = unencrypted): ")

    seed = hashlib.pbkdf2_hmac(
        "sha512",
        unicodedata.normalize("NFKD", phrase).encode(),
        ("mnemonic" + unicodedata.normalize("NFKD", bip39_pass)).encode(),
        2048,
        64,
    )

    chain = rpc(cli, ["getblockchaininfo"])["chain"]
    xprv = master_xprv(seed, chain != "main")

    rpc(
        cli,
        ["createwallet", WALLET, "false", "true"],
        secret=wallet_pass if wallet_pass else None,
    )

    if wallet_pass:
        cmd = [cli, f"-rpcwallet={WALLET}", "-stdinwalletpassphrase", "walletpassphrase", "60"]
        p = subprocess.run(cmd, input=wallet_pass + "\n", text=True, capture_output=True)
        if p.returncode:
            fail(p.stderr.strip() or p.stdout.strip())

    try:
        added = rpc(cli, ["addhdkey"], wallet=WALLET, secret=xprv)
        xpub = added["xpub"]
        for address_type in TYPES:
            rpc(
                cli,
                ["createwalletdescriptor", address_type, json.dumps({"hdkey": xpub})],
                wallet=WALLET,
            )
    finally:
        if wallet_pass:
            rpc(cli, ["walletlock"], wallet=WALLET)

    print(f"Imported BIP39 wallet into Bitcoin Core wallet: {WALLET}")


if __name__ == "__main__":
    main()
