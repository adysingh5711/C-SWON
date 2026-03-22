"""
verify/generate.py — Coldkey Message Signer (C-SWON verification utility)

Generates a cryptographically signed message using a Bittensor coldkey wallet.
Used to prove ownership of a wallet address off-chain (e.g. for subnet
participant verification or dispute resolution).

Usage:
    python verify/generate.py --name <wallet_name> --message "I acknowledge the C-SWON rules"

Outputs:
    Prints the signed message to stdout.
    Saves the message and signature to `message_and_signature.txt`.
    The signature can be verified with `verify/verify.py`.

See also:
    verify/verify.py — verifies signatures produced by this script.
"""

from datetime import datetime

import bittensor

# Hardcode or set the environment variable WALLET_PASS to the password for the wallet
# environ["WALLET_PASS"] = ""


def main(args):
    wallet = bittensor.Wallet(name=args.name)
    keypair = wallet.coldkey

    timestamp = datetime.now()
    timezone = timestamp.astimezone().tzname()

    # ensure compatiblity with polkadotjs messages, as polkadotjs always wraps message
    message = (
        "<Bytes>" + f"On {timestamp} {timezone} {args.message}" + "</Bytes>"
    )
    signature = keypair.sign(data=message)

    file_contents = f"{message}\n\tSigned by: {keypair.ss58_address}\n\tSignature: {signature.hex()}"
    print(file_contents)
    open("message_and_signature.txt", "w").write(file_contents)

    print("Signature generated and saved to message_and_signature.txt")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a signature")
    parser.add_argument("--message", help="The message to sign", type=str)
    parser.add_argument("--name", help="The wallet name", type=str)
    args = parser.parse_args()

    main(args)
