"""
NexSight AI — Launch Script
Microsoft Build AI Hackathon 2025

Usage:
  python run.py            # Default: port 8000
  python run.py --port 8080
  python run.py --reload   # Dev mode with auto-reload
"""

import sys
import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="NexSight AI Server")
    parser.add_argument("--port",   type=int, default=8000)
    parser.add_argument("--host",   default="0.0.0.0")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev mode)")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    print("\n" + "═" * 60)
    print("  NexSight AI — Manufacturing Intelligence Platform")
    print("  Microsoft Build AI Hackathon 2025")
    print("═" * 60)
    print(f"  URL:       http://localhost:{args.port}")
    print(f"  API Docs:  http://localhost:{args.port}/api/docs")
    print(f"  WebSocket: ws://localhost:{args.port}/ws/live")
    print(f"  Alerts SSE:http://localhost:{args.port}/api/stream/alerts")
    print("═" * 60 + "\n")

    cmd = [
        sys.executable, "-m", "uvicorn",
        "backend.main:app",
        "--host", args.host,
        "--port", str(args.port),
        "--log-level", "info",
    ]
    if args.reload:
        cmd.append("--reload")
    if args.workers > 1 and not args.reload:
        cmd += ["--workers", str(args.workers)]

    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        print("\n\nNexSight AI server stopped.\n")

if __name__ == "__main__":
    main()
