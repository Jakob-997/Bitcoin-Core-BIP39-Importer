#!/bin/sh
set -eu

here=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
archive="$here/../bitcoin-32.0rc2-x86_64-linux-gnu.tar.gz"
hash="0255103718033e6aee15fa944717fc277e047b845bff1e7408af0ea732d8d0c1"
walletdir="$here/wallet"

case "${1-}" in
    "") ;;
    --bip39-passphrase) ;;
    *) echo "Usage: ./tails.sh [--bip39-passphrase]"; exit 1 ;;
esac
[ "$#" -le 1 ] || { echo "Usage: ./tails.sh [--bip39-passphrase]"; exit 1; }

umask 077
[ ! -e "$walletdir" ] || { echo "wallet/ already exists"; exit 1; }

python3 -c 'from mnemonic import Mnemonic; from electrum.bip32 import BIP32Node' ||
    { echo "Required Tails Python modules not found"; exit 1; }

nmcli networking off
[ "$(LC_ALL=C nmcli networking)" = "disabled" ] ||
    { echo "Failed to disable networking"; exit 1; }
printf '%s  %s\n' "$hash" "$archive" | sha256sum --check

state=$(mktemp -d /dev/shm/core-bip39.XXXXXX)
cleanup() {
    [ -x "$state/core/bin/bitcoin-cli" ] &&
        "$state/core/bin/bitcoin-cli" stop >/dev/null 2>&1 || true
    rm -rf "$state"
}
trap cleanup EXIT HUP INT TERM

mkdir "$state/core" "$walletdir"
tar -xzf "$archive" -C "$state/core" --strip-components=1 --no-same-owner
export HOME="$state"

"$state/core/bin/bitcoind" -daemonwait -networkactive=0 -listen=0 -walletdir="$walletdir"
python3 "$here/generator.py" "$state/core/bin/bitcoin-cli" "$@"
"$state/core/bin/bitcoin-cli" stop

trap - EXIT HUP INT TERM
rm -rf "$state"
echo "Done."
