from __future__ import annotations

import argparse
import asyncio
import logging
import shutil
import sys

from .settings import ROOT, Settings


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


def cmd_enrich(args: argparse.Namespace) -> int:
    from .db import Database
    from .details import DetailsStore, EnrichManager, enrich_targets
    from .discogs import DiscogsClient
    from .models import Scheme

    settings = Settings()
    if not settings.discogs_username:
        print("set DISCOGS_USERNAME (and DISCOGS_TOKEN) in .env first", file=sys.stderr)
        return 2
    if not settings.db_path.is_file():
        print(f"no collection at {settings.db_path}; run `recordshelf sync` first", file=sys.stderr)
        return 2
    # The shelf database is only read, through a read-only connection.
    db = Database(settings.db_path, readonly=True)
    try:
        scheme = Scheme.model_validate(db.get_json("scheme") or {})
        targets = enrich_targets(db.list_releases(), scheme, db.get_overrides(), db.get_order())
    finally:
        db.close()
    if args.shelf_only:
        targets = [t for t in targets if t.shelf]
    if args.limit:
        targets = targets[: args.limit]
    shelf = sum(1 for t in targets if t.shelf)
    print(f"{len(targets)} releases ({shelf} shelf records first) -> {settings.details_path}")
    logging.getLogger("httpx").setLevel(logging.WARNING)  # one INFO line per request otherwise
    tty = sys.stdout.isatty()

    def factory() -> DiscogsClient:
        return DiscogsClient(settings.discogs_username, settings.discogs_token, settings.user_agent)

    def progress(st) -> None:
        if st.state != "running" or not st.total:
            return
        line = (
            f"{st.done}/{st.total} · {st.fetched} fetched · {st.prices} prices · "
            f"{st.cached} cached · {st.errors} errors"
        )
        if tty:
            print(f"\r{line} · {(st.current or '')[:40]:<40}", end="", flush=True)
        elif st.done and (st.done % 25 == 0 or st.done == st.total):
            print(line, flush=True)

    async def run() -> int:
        store = DetailsStore(settings.details_path)
        mgr = EnrichManager(store, factory, on_change=progress)
        mgr.start(targets, refresh_days=args.refresh_days, prices=not args.no_prices)
        st = await mgr.wait()
        counts = store.counts()
        store.close()
        if tty:
            print()
        if st.prices_skipped:
            print(f"price suggestions skipped: {st.prices_skipped}")
        print(
            f"{st.fetched} fetched, {st.prices} prices, {st.cached} already cached, "
            f"{st.errors} errors; cache holds {counts['release']} releases, "
            f"{counts['prices']} price sets, {counts['failed']} not found"
        )
        if st.state == "error":
            print(f"enrich stopped: {st.error}", file=sys.stderr)
            return 1
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
    env = ROOT / ".env"
    example = ROOT / ".env.example"
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

    p = sub.add_parser(
        "enrich",
        help="fetch full release details (credits, pressing, prices) into a separate cache",
        description="Resumable: releases already in the cache are skipped. Shelf records first.",
    )
    p.add_argument("--refresh-days", type=float, help="refetch entries older than this")
    p.add_argument("--no-prices", action="store_true", help="skip marketplace price suggestions")
    p.add_argument(
        "--shelf-only", action="store_true", help="only records that belong on the shelf"
    )
    p.add_argument("--limit", type=int, help="stop after this many releases")
    p.set_defaults(fn=cmd_enrich)

    p = sub.add_parser("init", help="write config/shelf.yaml and .env from the examples")
    p.set_defaults(fn=cmd_init)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
