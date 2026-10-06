# Bitcoin Core BIP39 Importer

Minimal BIP39 import overlay for Bitcoin Core.

It does one thing:

`BIP39 mnemonic -> BIP32 master key -> Bitcoin Core -> standard Core descriptors`

Bitcoin Core remains responsible for the wallet, child derivation, descriptors, address generation, key storage, and signing. The helper only performs the BIP39-to-BIP32 conversion Core does not expose directly.

Built with the [Bitcoin Core Feature Overlay](https://github.com/Jakob-997/Bitcoin-Core-Feature-Overlay) pattern.

## Files

- `generator.py` — validates the mnemonic, derives the BIP32 master xprv, and imports it into Core.
- `tails.sh` — verifies the pinned Core archive, disables networking, starts isolated Core, runs the generator, and stops Core.
- `bip39_english.txt` — official BIP39 English wordlist.

## Bitcoin Core

Pinned to Bitcoin Core 32.0rc2 Linux x86_64:

```
bitcoin-32.0rc2-x86_64-linux-gnu.tar.gz
SHA256 0255103718033e6aee15fa944717fc277e047b845bff1e7408af0ea732d8d0c1
```

Put that archive beside `tails.sh` before going offline.

## Run

```bash
chmod +x tails.sh
./tails.sh
```

The script creates `wallet/bip39-import`.

For meaningful funds, use a physically air-gapped machine. The launcher disables networking as defense in depth; software network controls are not a substitute for a physical air gap.
