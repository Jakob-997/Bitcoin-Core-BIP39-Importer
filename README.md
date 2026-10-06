# Bitcoin Core BIP39 Importer

Minimal BIP39 import overlay for Bitcoin Core.

`BIP39 mnemonic -> BIP32 master xprv -> Bitcoin Core -> standard Core descriptors`

The importer does not implement BIP39 or BIP32 itself:

- BIP39 validation and seed derivation use Trezor's `python-mnemonic`.
- BIP32 master-key conversion uses Electrum's `BIP32Node`, already shipped with Tails.
- Bitcoin Core receives the master xprv with `addhdkey` and creates the standard descriptor families with `createwalletdescriptor`.

Built with the [Bitcoin Core Feature Overlay](https://github.com/Jakob-997/Bitcoin-Core-Feature-Overlay) pattern.

## Run

Default: no BIP39 passphrase.

```bash
chmod +x tails.sh
./tails.sh
```

To use a BIP39 passphrase, opt in explicitly:

```bash
./tails.sh --bip39-passphrase
```

## Bitcoin Core

Pinned to Bitcoin Core 32.0rc2 Linux x86_64:

```text
bitcoin-32.0rc2-x86_64-linux-gnu.tar.gz
SHA256 0255103718033e6aee15fa944717fc277e047b845bff1e7408af0ea732d8d0c1
```

Put the archive **next to the project folder**, not inside it:

```text
~/bitcoin-32.0rc2-x86_64-linux-gnu.tar.gz
~/Bitcoin-Core-BIP39-Importer-main/
    generator.py
    README.md
    tails.sh
```

Then enter the project folder and run `./tails.sh`.

The script creates `wallet/bip39-import`.

For meaningful funds, use a physically air-gapped machine. The launcher disables networking as defense in depth; software network controls are not a substitute for a physical air gap.
