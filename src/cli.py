"""CLI Management and diagnostic utility."""
import argparse
import json
import os
import sys
import urllib.request
from .config import Config

def main():
    parser = argparse.ArgumentParser(description="Claude OpenRouter Management Utility")
    parser.add_argument("--status", action="store_true", help="Display real-time model pool status and cooldowns")
    parser.add_argument("--set-key", type=str, help="Set OpenRouter API Key")
    parser.add_argument("--test", action="store_true", help="Test OpenRouter connection with free tier")
    args = parser.parse_args()

    cfg = Config()

    if args.set_key:
        cfg.api_key = args.set_key
        print(f"[OK] API Key updated successfully in {cfg.config_path}")
        return

    if args.status:
        try:
            req = urllib.request.Request(f"http://127.0.0.1:{cfg.port}/status")
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.load(resp)
            print("=" * 80)
            print("          OPENROUTER FREE MODELS POOL & FAILOVER HEALTH           ")
            print("=" * 80)
            print(f"{'#':<3} {'Model Name':<45} {'Status':<12} {'Success':<8} {'Fail':<6} {'Cooldown'}")
            print("-" * 80)
            for i, m in enumerate(data.get("pool", []), 1):
                cd = f"{m['cooldown_remaining_sec']}s" if m.get("cooldown_remaining_sec", 0) > 0 else "-"
                print(f"{i:<3} {m['model']:<45} {m['status']:<12} {m['success_count']:<8} {m['fail_count']:<6} {cd}")
            print("=" * 80)
        except Exception:
            print("[Info] Bridge is not currently running. Start a session with `claude` to boot it.")
        return

    if args.test:
        if not cfg.api_key:
            print("[Error] No API key configured. Run with --set-key <your_key>")
            return
        print("[Testing] Contacting OpenRouter API...")
        try:
            req = urllib.request.Request(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {cfg.api_key}"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                d = json.load(resp)
                print("[SUCCESS] API Key is valid!")
                print("Key Label:", d.get("data", {}).get("label"))
                print("Free Tier:", d.get("data", {}).get("is_free_tier"))
        except Exception as e:
            print(f"[FAILED] Could not authenticate with OpenRouter: {e}")
        return

    parser.print_help()

if __name__ == "__main__":
    main()
