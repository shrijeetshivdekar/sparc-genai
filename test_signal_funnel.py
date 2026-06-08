"""Diagnose where articles are dropped in the signal pipeline funnel."""
import sys, os
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from startup_shield_web.server import (
    _fetch_direct_rss_signal_articles,
    _fetch_google_news_signal_articles,
    _fetch_gdelt_signal_articles,
    _looks_generic_signal_article,
    _classify_signal,
    _match_signal_company,
    _is_plausible_signal_company,
    _verified_profiles,
)

LIMIT = 30
FETCH = max(LIMIT * 4, 80)
WIN = 30

profiles = _verified_profiles()

print("Fetching three sources in parallel...")
with ThreadPoolExecutor(max_workers=3) as ex:
    f_rss = ex.submit(_fetch_direct_rss_signal_articles, limit=FETCH, window_days=WIN)
    f_gn  = ex.submit(_fetch_google_news_signal_articles, limit=FETCH, window_days=WIN)
    f_gd  = ex.submit(_fetch_gdelt_signal_articles, limit=FETCH)
    rss   = f_rss.result()
    gnews = f_gn.result()
    try: gdelt = f_gd.result()
    except Exception: gdelt = []

print(f"\nRaw fetched: RSS={len(rss)}, GN={len(gnews)}, GDELT={len(gdelt)}")

# Merge with URL dedup
seen = set(); articles = []
for batch in (rss, gnews, gdelt):
    for a in batch:
        k = (a.get("url") or a.get("title") or "").strip().lower()
        if k and k not in seen:
            seen.add(k); articles.append(a)

n0 = len(articles)
print(f"After URL/title dedup: {n0}")

# Step 1: generic article filter
step1_drops = []
step1_kept = []
for a in articles:
    if _looks_generic_signal_article(a):
        step1_drops.append(a)
    else:
        step1_kept.append(a)
print(f"\n[1] generic-article filter: kept {len(step1_kept)}, dropped {len(step1_drops)}")

# Step 2: classify - market_news means no real rule matched
step2_market_news = []
step2_real_rule = []
for a in step1_kept:
    rule = _classify_signal(a)
    if rule.get("id") == "market_news":
        step2_market_news.append((a, rule))
    else:
        step2_real_rule.append((a, rule))
print(f"[2] classifier: matched a real rule = {len(step2_real_rule)}, fell through to market_news = {len(step2_market_news)}")

# Step 3: company extraction - drop generics
step3_drops_generic = []
step3_drops_implausible = []
step3_kept = []
for a, rule in step2_real_rule:
    company, base_profile = _match_signal_company(a, profiles)
    if not company or company.lower() in ("india", "indian startup", "startup"):
        step3_drops_generic.append((a, rule, company))
        continue
    if not _is_plausible_signal_company(company, base_profile):
        step3_drops_implausible.append((a, rule, company))
        continue
    step3_kept.append((a, rule, company, base_profile))
print(f"[3] company extraction: kept {len(step3_kept)}, generic-name drops {len(step3_drops_generic)}, implausible-name drops {len(step3_drops_implausible)}")

# Step 4: dedup by normalized company
import re
def _norm(name):
    s = re.sub(r"\s+", " ", str(name or "").lower().strip())
    for sfx in (" pvt ltd"," private limited"," pvt. ltd."," pvt. ltd"," ltd."," ltd"," technologies"," technology"," solutions"," services"," digital"," robotics"," systems"," ventures"," labs"," ai"," fintech"):
        if s.endswith(sfx): s = s[:-len(sfx)].strip()
    return s

best = {}
for a, rule, company, base in step3_kept:
    nc = _norm(company)
    prev = best.get(nc)
    if prev is None or rule.get("confidence", 50) > prev[1].get("confidence", 50):
        best[nc] = (company, rule, a)
print(f"[4] company dedup (normalized): {len(best)} unique companies (from {len(step3_kept)} articles)")

# Show samples of biggest losses
print("\n--- Sample dropped-as-market_news (first 8) ---")
for a, _ in step2_market_news[:8]:
    print(f"  {a.get('title','')[:110]}")

print("\n--- Sample implausible-company drops (first 8) ---")
for a, _, company in step3_drops_implausible[:8]:
    print(f"  company='{company}'  title='{a.get('title','')[:90]}'")

print("\n--- Final 16 winners ---")
for nc, (company, rule, a) in sorted(best.items(), key=lambda kv: kv[1][1].get('confidence',50), reverse=True):
    print(f"  {rule.get('label'):35s} {company:30s}  conf={rule.get('confidence',50)}")
