from __future__ import annotations

import argparse
import asyncio
import logging
import shutil
import sys
from pathlib import Path

from .settings import Settings


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    settings = Settings()
    if args.reload:
        uvicorn.run(
            "recordshelf.app:create_app",
            factory=True,
            host=args.host or settings.host,
            port=args.port or settings.port,
            reload=True,
            reload_dirs=["src"],
        )
    else:
        from .app import create_app

        uvicorn.run(
            create_app(settings), host=args.host or settings.host, port=args.port or settings.port
        )
    return 0


def cmd_sync(args: argparse.Namespace) -> int:
    from .db import Database
    from .discogs import DiscogsClient, SyncManager

    settings = Settings()
    db = Database(settings.db_path)

    def factory() -> DiscogsClient:
        return DiscogsClient(settings.discogs_username, settings.discogs_token, settings.user_agent)

    def progress(status) -> None:
        if status.state == "running" and status.pages:
            print(
                f"\rpage {status.page}/{status.pages} ({status.fetched} records)",
                end="",
                flush=True,
            )

    async def run() -> int:
        mgr = SyncManager(db, factory, on_change=progress)
        mgr.start()
        status = await mgr.wait()
        print()
        if status.state == "error":
            print(f"sync failed: {status.error}", file=sys.stderr)
            return 1
        print(f"synced: {status.added} added, {status.updated} updated, {status.removed} removed")
        return 0

    return asyncio.run(run())


def cmd_init(args: argparse.Namespace) -> int:
    from .layout import EXAMPLE_YAML

    settings = Settings()
    layout = settings.layout_file
    if layout.exists():
        print(f"{layout} already exists")
    else:
        layout.parent.mkdir(parents=True, exist_ok=True)
        layout.write_text(EXAMPLE_YAML)
        print(f"wrote {layout}")
    env = Path(".env")
    example = Path(".env.example")
    if env.exists():
        print(".env already exists")
    elif example.exists():
        shutil.copy(example, env)
        print("wrote .env from .env.example; fill in DISCOGS_USERNAME and DISCOGS_TOKEN")
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(prog="recordshelf", description="recordShelf server and tools")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("serve", help="run the web server")
    p.add_argument("--host")
    p.add_argument("--port", type=int)
    p.add_argument("--reload", action="store_true", help="auto-reload on code changes (dev)")
    p.set_defaults(fn=cmd_serve)

    p = sub.add_parser("sync", help="download the Discogs collection now")
    p.set_defaults(fn=cmd_sync)

    p = sub.add_parser("init", help="write config/shelf.yaml and .env from the examples")
    p.set_defaults(fn=cmd_init)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
