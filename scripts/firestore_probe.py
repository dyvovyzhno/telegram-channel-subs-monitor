"""One-off probe for the Firestore hang seen in get_last_hash_from_firebase.

Runs the exact query the app makes, with a hard timeout, logs how long
it took and which leg failed. Not used in production.

Modes:
  sync  — plain blocking call in main thread (default).
  async — same call dispatched from inside asyncio.run(), matching main.py.
"""

import argparse
import asyncio
import signal
import time
import traceback

import firebase_admin
from firebase_admin import credentials, firestore

TIMEOUT_S = 20


# Mimic firebase_methods.py: initialize at module import, before any event loop.
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)
db = firestore.client()


def _query():
    return (
        db.collection("admin_actions")
        .order_by("date", direction=firestore.Query.DESCENDING)
        .limit(1)
        .get()
    )


def _probe_sync():
    t = time.monotonic()
    result = _query()
    print(f"[probe:sync] query OK in {time.monotonic() - t:.2f}s, docs={len(result)}")
    if result:
        data = result[0].to_dict()
        print(f"[probe:sync] last date={data.get('date')!r} hash={data.get('hash')!r}")


async def _probe_async():
    t = time.monotonic()
    # Exactly how main.py calls it from inside job(): blocking call on the loop thread.
    result = _query()
    print(f"[probe:async] query OK in {time.monotonic() - t:.2f}s, docs={len(result)}")
    if result:
        data = result[0].to_dict()
        print(f"[probe:async] last date={data.get('date')!r} hash={data.get('hash')!r}")


def _install_alarm():
    def _handler(signum, frame):
        raise TimeoutError(f"probe hang — no response within {TIMEOUT_S}s")

    signal.signal(signal.SIGALRM, _handler)
    signal.alarm(TIMEOUT_S)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=("sync", "async"), default="sync")
    parser.add_argument(
        "--idle",
        type=int,
        default=0,
        help="seconds to sleep between client init and query",
    )
    args = parser.parse_args()

    if args.idle > 0:
        print(f"[probe] idling {args.idle}s before query to let gRPC channel age...")
        time.sleep(args.idle)

    _install_alarm()
    try:
        if args.mode == "sync":
            _probe_sync()
        else:
            asyncio.run(_probe_async())
    except TimeoutError as e:
        print(f"[probe:{args.mode}] HUNG: {e}")
        print(f"[probe:{args.mode}] this reproduces the main.py symptom under mode={args.mode}")
    except Exception:
        print(f"[probe:{args.mode}] FAILED with exception:")
        traceback.print_exc()
    finally:
        signal.alarm(0)


if __name__ == "__main__":
    main()
