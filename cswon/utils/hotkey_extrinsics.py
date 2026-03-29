import asyncio
import ipaddress
import os
import socket
import subprocess
from typing import Sequence, Tuple
from urllib.parse import urlparse

import numpy as np


BAD_SIGNATURE_MARKER = "Transaction has a bad signature"
LOCAL_CHAIN_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0"}


def is_bad_signature_error(message: str) -> bool:
    return BAD_SIGNATURE_MARKER in (message or "")


def should_use_btcli_hotkey_extrinsics(*targets: str | None) -> bool:
    for target in targets:
        if not target:
            continue
        normalized = str(target).strip().lower()
        if normalized == "local":
            return True
        if "://" not in normalized:
            continue
        try:
            parsed = urlparse(normalized)
        except ValueError:
            continue
        if (parsed.hostname or "").lower() in LOCAL_CHAIN_HOSTS:
            return True
    return False


def _is_usable_local_axon_ip(candidate: str | None) -> bool:
    if not candidate:
        return False
    try:
        parsed = ipaddress.ip_address(candidate)
    except ValueError:
        return False
    return (
        parsed.version == 4
        and not parsed.is_loopback
        and not parsed.is_link_local
        and not parsed.is_unspecified
        and not parsed.is_multicast
    )


def _iter_interface_ipv4_candidates() -> list[str]:
    candidates: list[str] = []
    commands = [
        ["ifconfig"],
        ["hostname", "-I"],
        ["ip", "-o", "-4", "addr", "show"],
    ]
    for command in commands:
        try:
            output = subprocess.check_output(
                command,
                stderr=subprocess.DEVNULL,
                text=True,
            )
        except Exception:
            continue
        for token in output.replace("/", " ").split():
            if _is_usable_local_axon_ip(token) and token not in candidates:
                candidates.append(token)
    return candidates


def get_preferred_local_axon_ip() -> str | None:
    candidates: list[str] = []

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            # UDP connect resolves the preferred outbound interface without
            # requiring a successful remote handshake.
            sock.connect(("192.0.2.1", 1))
            outbound_ip = sock.getsockname()[0]
            if _is_usable_local_axon_ip(outbound_ip):
                candidates.append(outbound_ip)
    except OSError:
        pass

    for candidate in _iter_interface_ipv4_candidates():
        if candidate not in candidates:
            candidates.append(candidate)

    private_candidates = [
        candidate
        for candidate in candidates
        if ipaddress.ip_address(candidate).is_private
    ]
    if private_candidates:
        return private_candidates[0]
    return candidates[0] if candidates else None


def _restore_env(name: str, previous: str | None) -> None:
    if previous is None:
        os.environ.pop(name, None)
    else:
        os.environ[name] = previous


async def _serve_axon_via_btcli_async(
    *,
    wallet_name: str,
    wallet_hotkey: str,
    wallet_path: str,
    network: str,
    netuid: int,
    ip: str,
    port: int,
) -> Tuple[bool, str]:
    from bittensor_wallet import Wallet as CliWallet
    from bittensor_cli.src.bittensor.extrinsics.serving import set_axon_extrinsic
    from bittensor_cli.src.bittensor.subtensor_interface import SubtensorInterface

    disk_cache_before = os.environ.get("DISK_CACHE")
    os.environ["DISK_CACHE"] = "0"
    try:
        wallet = CliWallet(name=wallet_name, hotkey=wallet_hotkey, path=wallet_path)
        async with SubtensorInterface(network, use_disk_cache=False) as subtensor:
            success, message, _ = await set_axon_extrinsic(
                subtensor=subtensor,
                wallet=wallet,
                netuid=netuid,
                ip=ip,
                port=port,
                prompt=False,
                quiet=True,
                wait_for_inclusion=True,
                wait_for_finalization=True,
            )
            return success, message
    finally:
        _restore_env("DISK_CACHE", disk_cache_before)


def serve_axon_via_btcli(
    *,
    wallet,
    network: str,
    netuid: int,
    ip: str,
    port: int,
) -> Tuple[bool, str]:
    return asyncio.run(
        _serve_axon_via_btcli_async(
            wallet_name=wallet.name,
            wallet_hotkey=wallet.hotkey_str,
            wallet_path=wallet.path,
            network=network,
            netuid=netuid,
            ip=ip,
            port=port,
        )
    )


async def _set_weights_via_btcli_async(
    *,
    wallet_name: str,
    wallet_hotkey: str,
    wallet_path: str,
    network: str,
    netuid: int,
    uids: Sequence[int],
    weights: Sequence[float],
    version_key: int,
) -> Tuple[bool, str]:
    from bittensor_wallet import Wallet as CliWallet
    from bittensor_cli.src.bittensor.subtensor_interface import SubtensorInterface
    from bittensor_cli.src.commands.weights import SetWeightsExtrinsic
    from bittensor_cli.src.bittensor.extrinsics.root import (
        convert_weights_and_uids_for_emit,
    )

    disk_cache_before = os.environ.get("DISK_CACHE")
    os.environ["DISK_CACHE"] = "0"
    try:
        wallet = CliWallet(name=wallet_name, hotkey=wallet_hotkey, path=wallet_path)
        async with SubtensorInterface(network, use_disk_cache=False) as subtensor:
            uids_arr = np.asarray(list(uids), dtype=np.int64)
            weights_arr = np.asarray(list(weights), dtype=np.float32)
            extrinsic = SetWeightsExtrinsic(
                subtensor=subtensor,
                wallet=wallet,
                netuid=netuid,
                proxy=None,
                uids=uids_arr,
                weights=weights_arr,
                salt=[],
                version_key=version_key,
                prompt=False,
                decline=False,
                quiet=True,
                wait_for_inclusion=True,
                wait_for_finalization=True,
            )
            try:
                success, message, _ = await extrinsic.set_weights_extrinsic()
            except Exception as e:
                err_str = str(e).lower()
                # Fall back to raw set_weights when the CLI extrinsic fails
                # for commit-reveal related reasons on local chains:
                is_cr_missing = "get_commit_reveal_weights_enabled" in err_str
                is_bad_sig = "bad signature" in err_str
                if not (is_cr_missing or is_bad_sig):
                    raise

                weight_uids, weight_vals = convert_weights_and_uids_for_emit(
                    uids_arr, weights_arr
                )
                call = await subtensor.substrate.compose_call(
                    call_module="SubtensorModule",
                    call_function="set_weights",
                    call_params={
                        "dests": weight_uids,
                        "weights": weight_vals,
                        "netuid": netuid,
                        "version_key": version_key,
                    },
                )
                success, message, _ = await subtensor.sign_and_send_extrinsic(
                    call=call,
                    sign_with="hotkey",
                    wallet=wallet,
                    era={"period": 5},
                    wait_for_inclusion=True,
                    wait_for_finalization=True,
                    proxy=None,
                )
            return success, message
    finally:
        _restore_env("DISK_CACHE", disk_cache_before)


def set_weights_via_btcli(
    *,
    wallet,
    network: str,
    netuid: int,
    uids: Sequence[int],
    weights: Sequence[float],
    version_key: int,
) -> Tuple[bool, str]:
    return asyncio.run(
        _set_weights_via_btcli_async(
            wallet_name=wallet.name,
            wallet_hotkey=wallet.hotkey_str,
            wallet_path=wallet.path,
            network=network,
            netuid=netuid,
            uids=uids,
            weights=weights,
            version_key=version_key,
        )
    )
