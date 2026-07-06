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

NOTE: the endpoint is undocumented; request/response details follow
Claude-Code-Usage-Monitor (src/claude_monitor/output/api_usage.py).
The User-Agent header is REQUIRED — without it requests land in a
strict rate-limit bucket (429s). 180s polling is the safe cadence.
Access tokens live ~60 min; Claude Code / the desktop app refreshes
the Keychain while active, so the token is re-read on every cycle.

Usage:
    python3 tools/usage_bridge.py --once     # single shot + raw dump
    python3 tools/usage_bridge.py            # loop every 180s
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
INTERVAL_S = 180   # safe polling cadence per Claude-Code-Usage-Monitor #202


def get_access_token() -> str:
    """Read the OAuth token from the Keychain, failing loudly if expired.
    Tokens live ~60 min; running any `claude` command (or an active
    desktop app) refreshes the Keychain entry."""
    out = subprocess.run(
        ["security", "find-generic-password", "-s", "Claude Code-credentials", "-w"],
        capture_output=True, text=True, check=True,
    ).stdout.strip()
    oauth = json.loads(out)["claudeAiOauth"]
    expires_at = oauth.get("expiresAt")  # epoch milliseconds
    if expires_at:
        left_s = expires_at / 1000 - datetime.datetime.now().timestamp()
        if left_s <= 0:
            raise RuntimeError(
                "access token 已過期 — 跑任一 claude 指令(或讓桌面 app 活動一下)"
                "刷新 Keychain 後再試")
    return oauth["accessToken"]


def fetch_usage(token: str) -> dict:
    req = urllib.request.Request(USAGE_URL, headers={
        "Authorization": f"Bearer {token}",
        "anthropic-beta": "oauth-2025-04-20",
        # REQUIRED: requests without a claude-code UA hit a strict 429 bucket.
        "User-Agent": "claude-code/2.1.32",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.load(r)


def minutes_until(iso_ts: str) -> int:
    dt = datetime.datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
    delta = dt - datetime.datetime.now(datetime.timezone.utc)
    return max(0, int(delta.total_seconds() // 60))


def as_pct(v) -> int:
    """utilization arrives as 0-100 or 0-1 depending on account/version."""
    f = float(v)
    return round(f * 100) if f <= 1.0 else round(f)


def extract(raw: dict) -> dict:
    """Map the endpoint response to the device message. Shape per
    Claude-Code-Usage-Monitor: five_hour/seven_day {utilization,
    resets_at}, sometimes nested under rate_limits."""
    root = raw.get("rate_limits") or raw
    msg = {"cmd": "usage"}
    five = root.get("five_hour") or {}
    week = root.get("seven_day") or {}
    if five.get("utilization") is not None:
        msg["session_pct"] = as_pct(five["utilization"])
    if week.get("utilization") is not None:
        msg["week_pct"] = as_pct(week["utilization"])
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
