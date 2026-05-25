"""Benchmark sequential vs parallel signal-source fetching."""
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from startup_shield_web.server import (
    _fetch_direct_rss_signal_articles,
    _fetch_google_news_signal_articles,
    _fetch_gdelt_signal_articles,
)

LIMIT = 120
WINDOW = 30


def time_call(label, fn, *args, **kwargs):
    t0 = time.perf_counter()
    try:
        result = fn(*args, **kwargs)
        n = len(result)
        err = ""
    except Exception as exc:
        n = 0
        err = f"{type(exc).__name__}: {exc}"
        result = []
    elapsed = time.perf_counter() - t0
    print(f"  {label:20s} {elapsed:6.2f}s  ->  {n:3d} articles  {err}")
    return elapsed, result


def sequential():
    print("\n[SEQUENTIAL]")
    t0 = time.perf_counter()
    e1, r1 = time_call("RSS", _fetch_direct_rss_signal_articles, limit=LIMIT, window_days=WINDOW)
    e2, r2 = time_call("Google News", _fetch_google_news_signal_articles, limit=LIMIT, window_days=WINDOW)
    e3, r3 = time_call("GDELT", _fetch_gdelt_signal_articles, limit=LIMIT)
    total = time.perf_counter() - t0
    print(f"  {'TOTAL wall-clock':20s} {total:6.2f}s")
    return total, r1, r2, r3


def parallel():
    print("\n[PARALLEL]")
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=3) as ex:
        f_rss = ex.submit(_fetch_direct_rss_signal_articles, limit=LIMIT, window_days=WINDOW)
        f_gn  = ex.submit(_fetch_google_news_signal_articles, limit=LIMIT, window_days=WINDOW)
        f_gd  = ex.submit(_fetch_gdelt_signal_articles, limit=LIMIT)

        def collect(label, fut):
            tstart = time.perf_counter()
            try:
                res = fut.result()
                n = len(res)
                err = ""
            except Exception as exc:
                res = []
                n = 0
                err = f"{type(exc).__name__}: {exc}"
            elapsed = time.perf_counter() - tstart
            print(f"  {label:20s} (waited {elapsed:5.2f}s)  ->  {n:3d} articles  {err}")
            return res

        r1 = collect("RSS", f_rss)
        r2 = collect("Google News", f_gn)
        r3 = collect("GDELT", f_gd)
    total = time.perf_counter() - t0
    print(f"  {'TOTAL wall-clock':20s} {total:6.2f}s")
    return total, r1, r2, r3


if __name__ == "__main__":
    print(f"Limit per source: {LIMIT}, window_days: {WINDOW}")
    seq_total, *_ = sequential()
    par_total, *_ = parallel()
    print(f"\n=== Speedup: {seq_total / par_total:.2f}x ({seq_total - par_total:.2f}s saved) ===")
