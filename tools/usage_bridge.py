#!/usr/bin/env python3
"""Push real Claude rate-limit usage to the Stick Buddy over BLE.

The official desktop heartbeat has no usage %/reset fields, so this
bridge reads the same numbers Settings > Usage shows and writes an
extension message to the device's Nordic-UART RX characteristic:

    {"cmd":"usage","session_pct":33,"week_pct":12,"reset_in_min":178}

macOS CoreBluetooth shares one physical link per peripheral across
apps, so this works alongside the Claude Desktop connection — no
second BLE connection, no firmware pairing changes.

Credentials: the OAuth access token is read from the macOS Keychain
item "Claude Code-credentials" AT RUNTIME, under the invoking user's
authority (macOS will prompt on first access). The token never leaves
this machine except toward api.anthropic.com.

NOTE: the usage endpoint below is what community tools (ccusage,
Claude-Code-Usage-Monitor) use; it is NOT officially documented —
if the response shape differs, run with --once to see the raw JSON
and adjust extract().

Usage:
    pip install bleak
    python3 tools/usage_bridge.py --once     # single shot + raw dump
    python3 tools/usage_bridge.py            # loop every 60s
"""
import argparse
import asyncio
import datetime
import json
import subprocess
import sys
import urllib.request

DEVICE_NAME = "Claude-0B34"
NUS_RX = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"   # write
USAGE_URL = "https://api.anthropic.com/api/oauth/usage"
INTERVAL_S = 60


def get_access_token() -> str:
    out = subprocess.run(
        ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    creds = json.loads(out)
    return creds["claudeAiOauth"]["accessToken"]


def fetch_usage(token: str) -> dict:
    req = urllib.request.Request(USAGE_URL, headers={
        "Authorization": f"Bearer {token}",
        "anthropic-beta": "oauth-2025-04-20",
        "User-Agent": "stick-buddy-usage-bridge/1.0",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def minutes_until(iso_ts: str) -> int:
    dt = datetime.datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    delta = dt - datetime.datetime.now(datetime.timezone.utc)
    return max(0, int(delta.total_seconds() // 60))


def extract(raw: dict) -> dict:
    """Map the endpoint response to the device message. Adjust here if
    the (undocumented) response shape differs."""
    msg = {"cmd": "usage"}
    five = raw.get("five_hour") or {}
    week = raw.get("seven_day") or {}
    if "utilization" in five:
        msg["session_pct"] = round(five["utilization"])
    if "utilization" in week:
        msg["week_pct"] = round(week["utilization"])
    if five.get("resets_at"):
        msg["reset_in_min"] = minutes_until(five["resets_at"])
    return msg


async def send_ble(payload: str) -> None:
    from bleak import BleakClient, BleakScanner
    dev = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10)
    if dev is None:
        raise RuntimeError(f"BLE device {DEVICE_NAME} not found")
    async with BleakClient(dev) as client:
        await client.write_gatt_char(NUS_RX, (payload + "\n").encode(), response=False)


async def run(once: bool) -> int:
    token = get_access_token()
    while True:
        try:
            raw = fetch_usage(token)
            if once:
                print("raw response:", json.dumps(raw, indent=2)[:2000])
            msg = extract(raw)
            if len(msg) == 1:
                print("no recognized usage fields — see raw dump; extract() needs adjusting",
                      file=sys.stderr)
                return 1
            payload = json.dumps(msg)
            await send_ble(payload)
            print(f"sent: {payload}")
        except Exception as e:
            print(f"error: {e}", file=sys.stderr)
            if once:
                return 1
        if once:
            return 0
        await asyncio.sleep(INTERVAL_S)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true",
                    help="single fetch+send, print raw endpoint response")
    args = ap.parse_args()
    return asyncio.run(run(args.once))


if __name__ == "__main__":
    sys.exit(main())
