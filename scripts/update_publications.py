#!/usr/bin/env python3
"""
Refresh publications.json from Google Scholar and ORCID/OpenAlex.

Sources, in order (each one is optional; set only what you have):
  1. SerpAPI Google Scholar Author API   -> needs SCHOLAR_ID and SERPAPI_KEY (most reliable)
  2. `scholarly` direct scrape           -> needs SCHOLAR_ID (free, but Google sometimes blocks it)
  3. OpenAlex, looked up by your ORCID   -> needs ORCID_ID (free, very reliable, adds DOIs/full author lists)

Results are merged by title. If every source fails, the existing publications.json
is left untouched so the site never goes blank.

Environment variables:
  SCHOLAR_ID   Google Scholar user id (the value after "user=" in your profile URL)
  ORCID_ID     e.g. 0000-0002-1234-5678
  SERPAPI_KEY  optional, from serpapi.com (free tier covers a weekly sync)
  CONTACT_EMAIL optional, sent to OpenAlex as a courtesy (polite pool)
"""
import json, os, re, sys, time, datetime, difflib, urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "publications.json")
EXCLUDE = os.path.join(ROOT, "exclude.txt")

SCHOLAR_ID = os.environ.get("SCHOLAR_ID", "").strip()
ORCID_ID = os.environ.get("ORCID_ID", "").strip()
SERPAPI_KEY = os.environ.get("SERPAPI_KEY", "").strip()
EMAIL = os.environ.get("CONTACT_EMAIL", "").strip()


def load_exclude():
    """Lines in exclude.txt are title beginnings to hide (case and punctuation ignored)."""
    if not os.path.exists(EXCLUDE):
        return []
    with open(EXCLUDE, encoding="utf-8") as f:
        return [norm(l) for l in f if l.strip() and not l.lstrip().startswith("#")]


def keep(p, excluded):
    """Show everything except entries listed in exclude.txt."""
    t = norm(p.get("title"))
    return bool(t) and not any(t.startswith(x) for x in excluded)


def get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "academic-site-sync/1.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def norm(title):
    return re.sub(r"[^a-z0-9]", "", (title or "").lower())[:200]


def year_of(v):
    try:
        return int(str(v)[:4])
    except (TypeError, ValueError):
        return None


# ---------- 1. SerpAPI ----------
def from_serpapi():
    pubs, metrics, start = [], {}, 0
    while True:
        q = urllib.parse.urlencode({
            "engine": "google_scholar_author", "author_id": SCHOLAR_ID,
            "api_key": SERPAPI_KEY, "num": 100, "start": start, "sort": "pubdate",
        })
        d = get_json(f"https://serpapi.com/search.json?{q}")
        if start == 0:
            for row in d.get("cited_by", {}).get("table", []):
                if "citations" in row: metrics["citations"] = row["citations"].get("all")
                if "h_index" in row: metrics["h_index"] = row["h_index"].get("all")
                if "i10_index" in row: metrics["i10_index"] = row["i10_index"].get("all")
        arts = d.get("articles", [])
        for a in arts:
            pubs.append({
                "title": a.get("title"), "authors": a.get("authors", ""),
                "venue": a.get("publication", ""), "year": year_of(a.get("year")),
                "citations": (a.get("cited_by") or {}).get("value") or 0,
                "url": a.get("link", ""), "doi": "",
            })
        if len(arts) < 100:
            break
        start += 100
    return pubs, metrics


# ---------- 2. scholarly ----------
def from_scholarly():
    from scholarly import scholarly  # pip install scholarly
    author = scholarly.search_author_id(SCHOLAR_ID)
    author = scholarly.fill(author, sections=["basics", "indices", "publications"])
    metrics = {"citations": author.get("citedby"), "h_index": author.get("hindex"),
               "i10_index": author.get("i10index")}
    pubs = []
    for p in author.get("publications", []):
        bib = p.get("bib", {})
        pid = p.get("author_pub_id", "")
        pubs.append({
            "title": bib.get("title"), "authors": "",
            "venue": bib.get("citation", ""), "year": year_of(bib.get("pub_year")),
            "citations": p.get("num_citations", 0),
            "url": f"https://scholar.google.com/citations?view_op=view_citation&citation_for_view={pid}" if pid else "",
            "doi": "",
        })
    return pubs, metrics


# ---------- 3. OpenAlex by ORCID ----------
def from_openalex():
    pubs, cursor = [], "*"
    while cursor:
        params = {"filter": f"author.orcid:https://orcid.org/{ORCID_ID}", "per-page": 200, "cursor": cursor}
        if EMAIL: params["mailto"] = EMAIL
        d = get_json("https://api.openalex.org/works?" + urllib.parse.urlencode(params))
        for w in d.get("results", []):
            if w.get("type") in ("paratext", "peer-review", "erratum"):
                continue
            doi = (w.get("doi") or "").replace("https://doi.org/", "")
            src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name", "")
            pubs.append({
                "title": w.get("title") or w.get("display_name"),
                "authors": ", ".join(a["author"]["display_name"] for a in w.get("authorships", [])),
                "venue": src, "year": w.get("publication_year"),
                "citations": w.get("cited_by_count", 0),
                "url": f"https://doi.org/{doi}" if doi else (w.get("id") or ""),
                "doi": doi,
            })
        cursor = d.get("meta", {}).get("next_cursor")
        time.sleep(0.2)
    return pubs


def merge(primary, secondary):
    """Scholar is primary (citation counts, coverage); OpenAlex fills authors, DOI, venue."""
    by_title = {norm(p["title"]): p for p in primary if p.get("title")}
    for s in secondary:
        k = norm(s["title"])
        if k and k not in by_title:  # tolerate small title differences between databases
            close = difflib.get_close_matches(k, list(by_title), n=1, cutoff=0.9)
            if not close:  # one title is the other plus extra words (common on Scholar)
                close = [x for x in by_title if len(min(x, k, key=len)) >= 40 and (x.startswith(k) or k.startswith(x))]
            if close: k = close[0]
        if k in by_title:
            p = by_title[k]
            for f in ("authors", "doi", "venue", "year"):
                if not p.get(f) and s.get(f): p[f] = s[f]
            if s.get("doi"): p["url"] = p.get("url") or f"https://doi.org/{s['doi']}"
            p["citations"] = max(p.get("citations") or 0, s.get("citations") or 0)
        elif k:
            by_title[k] = s
    return list(by_title.values())


def main():
    scholar, metrics, used = [], {}, []
    if SCHOLAR_ID and SERPAPI_KEY:
        try:
            scholar, metrics = from_serpapi(); used.append("Google Scholar")
        except Exception as e:
            print("SerpAPI failed:", e, file=sys.stderr)
    if SCHOLAR_ID and not scholar:
        try:
            scholar, metrics = from_scholarly(); used.append("Google Scholar")
        except Exception as e:
            print("scholarly failed:", e, file=sys.stderr)

    openalex = []
    if ORCID_ID:
        try:
            openalex = from_openalex(); used.append("ORCID/OpenAlex")
        except Exception as e:
            print("OpenAlex failed:", e, file=sys.stderr)

    if not scholar and not openalex:
        print("No source returned data; leaving publications.json unchanged.")
        return 0

    # Keep entries already in publications.json (e.g. added by hand from your CV)
    # so a paper missing from Scholar/ORCID never drops off the site.
    existing, old_metrics = [], {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            old = json.load(f)
        existing = [p for p in old.get("publications", []) if not p.get("example")]
        old_metrics = old.get("metrics", {})
    if scholar:
        # Entries saved from Scholar earlier but no longer on the Scholar profile
        # (deleted or retitled there) are dropped, so the site follows Scholar.
        skeys = [norm(p.get("title")) for p in scholar]
        def still_on_scholar(p):
            if "scholar.google" not in (p.get("url") or ""):
                return True
            k = norm(p.get("title"))
            return k in skeys or bool(difflib.get_close_matches(k, skeys, n=1, cutoff=0.9))
        existing = [p for p in existing if still_on_scholar(p)]
    pubs = merge(merge(scholar, openalex), existing)
    pubs = merge([], pubs)  # final pass: fold together any remaining near-duplicates
    excluded = load_exclude()
    before = len(pubs)
    pubs = [p for p in pubs if keep(p, excluded)]
    print(f"Hid {before - len(pubs)} entries listed in exclude.txt.")

    if metrics.get("citations"):
        metrics["label"] = "Google Scholar"
    elif old_metrics.get("citations"):
        metrics = old_metrics  # Scholar unavailable this week: keep the last good figures
    else:
        cites = sorted((p.get("citations") or 0 for p in pubs), reverse=True)
        metrics = {
            "citations": sum(cites),
            "h_index": sum(1 for i, c in enumerate(cites, 1) if c >= i),
            "i10_index": sum(1 for c in cites if c >= 10),
            "label": "computed from listed citations",
        }

    pubs.sort(key=lambda p: (-(p.get("year") or 9999), (p.get("title") or "").lower()))
    data = {
        "source": " + ".join(used),
        "updated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "metrics": metrics,
        "publications": pubs,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(pubs)} publications from {data['source']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
