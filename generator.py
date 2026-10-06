#!/usr/bin/env python3
import getpass
import json
import subprocess
import sys

from electrum.bip32 import BIP32Node
from mnemonic import Mnemonic

DEFAULT_WALLET = "bip39-import"
TYPES = ("legacy", "p2sh-segwit", "bech32", "bech32m")


def cli(*args, stdin=None):
    p = subprocess.run(
        [sys.argv[1], *args],
        input=stdin,
        text=True,
        capture_output=True,
    )
    if p.returncode:
        raise SystemExit(p.stderr.strip() or p.stdout.strip())
    return p.stdout


if len(sys.argv) not in (2, 3) or (
    len(sys.argv) == 3 and sys.argv[2] != "--bip39-passphrase"
):
    raise SystemExit("Usage: tails.sh [--bip39-passphrase]")

bip39 = Mnemonic("english")
words = input("BIP39 mnemonic: ").strip()
if not bip39.check(words):
    raise SystemExit("Invalid BIP39 mnemonic.")

passphrase = getpass.getpass("BIP39 passphrase: ") if len(sys.argv) == 3 else ""
wallet = input(f"Wallet name [{DEFAULT_WALLET}]: ").strip() or DEFAULT_WALLET
seed = bip39.to_seed(words, passphrase)
xprv = BIP32Node.from_rootseed(seed, xtype="standard").to_xprv()

cli("createwallet", wallet, "false", "true")
added = json.loads(
    cli(f"-rpcwallet={wallet}", "-stdin", "addhdkey", stdin=xprv + "\n")
)
xpub = added["xpub"]

for address_type in TYPES:
    cli(
        f"-rpcwallet={wallet}",
        "createwalletdescriptor",
        address_type,
        json.dumps({"hdkey": xpub}),
    )

print(f"Imported BIP39 wallet into Bitcoin Core wallet: {wallet}")
