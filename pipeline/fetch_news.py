import os
import re
import json
import ssl
import hashlib
import difflib
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

# Certificate verification stays on. This previously used
# ssl._create_unverified_context(), which disabled TLS verification for every feed
# fetched — the output of those fetches is published straight to the CDN and read by
# every installed app, so an unauthenticated transport was the wrong trade for the
# occasional badly configured feed host.
SSL_CONTEXT = ssl.create_default_context()

# Global Statistics
STATS_TOTAL_RSS = 0
STATS_MATCHING_GTA6 = 0
STATS_DISCARDED = 0

# Constants
# Feed roster.
#
# The original list was six general gaming sites plus RockstarINTEL. Measured against
# live feeds, the general ones carry 1-8 GTA 6 mentions per 20-100 items, and the
# leak/rumour filter below then discards most of that — so the feed went stale between
# genuinely newsworthy posts. Where an outlet publishes a GTA-specific topic feed, that
# URL is used instead of the sitewide one: rockstarintel.com/category/gta-6/feed/ returns
# 123 GTA 6 mentions across 10 items versus 35 for its sitewide feed.
#
# "tier" records how much weight to give a source and is written to each article's
# "confidence" field:
#   high   - established outlet with a track record on Rockstar reporting
#   medium - legitimate outlet, more aggregation than original reporting
FEEDS = [
    # --- GTA-dedicated, highest signal ---
    {
        "id": "rockstarintel",
        "name": "RockstarINTEL",
        "category": "News",
        "tier": "high",
        "url": "https://rockstarintel.com/category/gta-6/feed/"
    },
    {
        "id": "dexerto_gta",
        "name": "Dexerto",
        "category": "News",
        "tier": "medium",
        "url": "https://www.dexerto.com/gta/feed/"
    },
    {
        "id": "gtaboom",
        "name": "GTABOOM",
        "category": "Rumor",
        "tier": "medium",
        "url": "https://gtaboom.com/feed/"
    },
    # --- Established outlets with a Rockstar reporting record ---
    {
        "id": "vgc",
        "name": "VGC",
        "category": "News",
        "tier": "high",
        "url": "https://www.videogameschronicle.com/feed/"
    },
    {
        "id": "insidergaming",
        "name": "Insider Gaming",
        "category": "Rumor",
        "tier": "high",
        "url": "https://insider-gaming.com/feed/"
    },
    {
        "id": "eurogamer",
        "name": "Eurogamer",
        "category": "News",
        "tier": "high",
        "url": "https://www.eurogamer.net/feed/news"
    },
    {
        "id": "gamespot",
        "name": "GameSpot",
        "category": "News",
        "tier": "high",
        "url": "https://www.gamespot.com/feeds/news/"
    },
    {
        "id": "ign",
        "name": "IGN",
        "category": "News",
        "tier": "high",
        "url": "https://feeds.feedburner.com/ign/news"
    },
    # --- Broader coverage, lower GTA density ---
    {
        "id": "videogamer",
        "name": "VideoGamer",
        "category": "News",
        "tier": "medium",
        "url": "https://www.videogamer.com/feed/"
    },
    {
        "id": "pushsquare",
        "name": "Push Square",
        "category": "News",
        "tier": "medium",
        "url": "https://www.pushsquare.com/feeds/latest"
    }
]

PRIMARY_KEYWORDS = ["gta 6", "grand theft auto vi", "grand theft auto 6"]
MAX_ARTICLES = 20
MAX_PER_SOURCE = 4  # keeps one high-volume outlet from filling the whole feed
MAX_AGE_DAYS = 180

# Published into the CDN repo's ota/ directory, which is what the app reads.
# It previously wrote to pipeline/speculative_feed.json in the app repo while the app
# fetched from a placeholder repo that did not exist, so the daily output reached nobody.
FEED_FILE_PATH = os.path.join("ota", "speculative_feed.json")

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def normalize_title(title):
    if not title:
        return ""
    title = title.lower()
    # Strip common news tags or prefixes
    title = re.sub(r'^(report|rumor|news|update|leak|gta 6|grand theft auto 6|grand theft auto vi)\s*:\s*', '', title)
    title = re.sub(r'\s*\(.+\)$', '', title)  # remove trailing parenthetical info
    title = re.sub(r'[^a-z0-9\s]', '', title)
    return " ".join(title.split())

def is_duplicate(article1, article2):
    # 1. Exact URL match
    if article1["url"] == article2["url"]:
        return True
    
    # 2. SequenceMatcher similarity for titles
    norm1 = normalize_title(article1["title"])
    norm2 = normalize_title(article2["title"])
    if difflib.SequenceMatcher(None, norm1, norm2).ratio() > 0.85:
        return True
        
    return False

def generate_id(title, url):
    key = f"{normalize_title(title)}|{url}"
    return hashlib.sha256(key.encode('utf-8')).hexdigest()

PRIMARY_PATTERN = re.compile(
    r'\b(gta\s*6|grand\s*theft\s*auto\s*vi|grand\s*theft\s*auto\s*6)\b', re.IGNORECASE
)

# Other franchises and GTA Online, which are not what this feed is for.
FRANCHISE_EXCLUSIONS = [re.compile(p, re.IGNORECASE) for p in [
    r'\bgta\s*online\b',
    r'\bgrand\s*theft\s*auto\s*online\b',
    r'\bred\s*dead\b',
    r'\bbully\b',
    r'\bmax\s*payne\b',
    r'\bl\.?a\.?\s*noire\b',
    r'\bmidnight\s*club\b',
    r'\bmanhunt\b',
    r'\bcall\s*of\s*duty\b',
    r'\bmodern\s*warfare\b',
]]

# Pure market/stock noise and affiliate-bait. Deliberately much shorter than the list
# this replaced: that one rejected pre-orders, marketing, legal, staffing and anything
# containing "guide" or "keys", which between them account for nearly all GTA 6 coverage
# four months out from launch.
NOISE_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r'\bshare\s*price\b',
    r'\bstock\s*(price|market)\b',
    r'\bmarket\s*cap\b',
    r'\bearnings\s*call\b',
    r'\bquarterly\s*(results|report)\b',
    r'\bshareholders?\b',
    r'\b(cd|game)\s*keys?\s*(deal|price|cheap|buy)\b',
    r'\bbest\s*(deals?|prices?)\b',
    r'\bdiscount\s*code\b',
]]

# Signals that an article is leak/rumour material rather than reported news.
LEAK_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r'\bleak(ed|s)?\b',
    r'\bdatamine(d|s|r|g)?\b',
    r'\bhidden\s+files?\b',
    r'\bfound\s+in\s+(the\s+)?files?\b',
    r'\bbeta\s*(build|version|test)\b',
    r'\buncover(ed|s)?\b',
]]

# "claims" and "hints" were tried here and removed: both appear constantly in ordinary
# reporting, and they pushed 12 of 20 articles into the Rumor bucket, including plain
# factual pieces. What remains actually distinguishes unconfirmed reporting.
RUMOR_PATTERNS = [re.compile(p, re.IGNORECASE) for p in [
    r'\brumou?r(ed|s)?\b',
    r'\binsider\s+(source|report|claim)',
    r'\bspeculat(e|ion|ive|es|ed)?\b',
    r'\breportedly\b',
    r'\ballegedly\b',
    r'\bunconfirmed\b',
]]


def is_gta6_relevant(title, description, source_id, url):
    """
    Whether an article belongs in the feed at all.

    This replaced a filter that required a leak/rumour/datamine keyword to be present.
    That made sense in 2023; measured against the live feeds in July 2026 it rejected
    every one of the 16 most recent GTA 6 articles from RockstarINTEL and Dexerto, because
    current coverage is pre-orders, marketing, dev interviews and physical-media stories.
    The gate is now "is this substantively about GTA 6", with only market noise excluded.
    Leak/rumour status is recorded via classify_article rather than used to include or drop.
    """
    if source_id == "rockstar" or "rockstargames.com" in url.lower():
        return False

    title_desc = f"{title} {description}"

    if not PRIMARY_PATTERN.search(title_desc):
        return False

    # Only drop a franchise mention when GTA 6 isn't the actual subject of the headline.
    if not PRIMARY_PATTERN.search(title):
        if any(pat.search(title_desc) for pat in FRANCHISE_EXCLUSIONS):
            return False

    if any(pat.search(title_desc) for pat in NOISE_PATTERNS):
        return False

    return True


def classify_article(title, description, feed_category):
    """Per-article category, so the UI badge reflects the story rather than the source."""
    title_desc = f"{title} {description}"
    if any(pat.search(title_desc) for pat in LEAK_PATTERNS):
        return "Leak"
    if any(pat.search(title_desc) for pat in RUMOR_PATTERNS):
        return "Rumor"
    return feed_category or "News"

def fetch_og_image(url):
    if not url:
        return None
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=3) as response:
            html = response.read().decode('utf-8', errors='ignore')
            # Look for og:image meta tag
            match = re.search(r'<meta\s+property=["\']og:image["\']\s+content=["\']([^"\']+)["\']', html)
            if not match:
                match = re.search(r'<meta\s+content=["\']([^"\']+)["\']\s+property=["\']og:image["\']', html)
            if match:
                return match.group(1).strip()
    except Exception as e:
        print(f"  Failed to fetch OG image for {url}: {e}")
    return None

def find_image(item, article_url):
    # namespaces for media elements
    namespaces = {
        'media': 'http://search.yahoo.com/mrss/'
    }

    # 1. Try media:thumbnail
    for elem in item.findall('.//{http://search.yahoo.com/mrss/}thumbnail'):
        url = elem.get('url')
        if url:
            return url.strip()
            
    # 2. Try Open Graph image (done on demand)
    og_img = fetch_og_image(article_url)
    if og_img:
        return og_img

    # 3. Try enclosure tag
    for elem in item.findall('enclosure'):
        url = elem.get('url')
        mime = elem.get('type', '')
        if url and ('image' in mime or url.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))):
            return url.strip()

    # 4. Try media:content
    for elem in item.findall('.//{http://search.yahoo.com/mrss/}content'):
        url = elem.get('url')
        medium = elem.get('medium')
        if url and (medium == 'image' or url.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))):
            return url.strip()

    return None

def parse_rss_feed(feed_info):
    articles = []
    print(f"Fetching: {feed_info['name']}...")
    try:
        req = urllib.request.Request(feed_info["url"], headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=10) as response:
            xml_data = response.read()
            
        root = ET.fromstring(xml_data)
        
        # Determine items
        items = root.findall('.//item')
        if not items:
            # Atom support fallback
            items = root.findall('.//{http://www.w3.org/2005/Atom}entry')
            is_atom = True
        else:
            is_atom = False
            
        now = datetime.now(timezone.utc)
        cutoff_date = now - timedelta(days=MAX_AGE_DAYS)
        
        for item in items:
            try:
                if is_atom:
                    title_elem = item.find('{http://www.w3.org/2005/Atom}title')
                    title = title_elem.text if title_elem is not None else ""
                    
                    link_elem = item.find('{http://www.w3.org/2005/Atom}link')
                    url = link_elem.get('href') if link_elem is not None else ""
                    
                    date_elem = item.find('{http://www.w3.org/2005/Atom}published') or item.find('{http://www.w3.org/2005/Atom}updated')
                    date_str = date_elem.text if date_elem is not None else ""
                    
                    desc_elem = item.find('{http://www.w3.org/2005/Atom}summary') or item.find('{http://www.w3.org/2005/Atom}content')
                    description = desc_elem.text if desc_elem is not None else ""
                else:
                    title_elem = item.find('title')
                    title = title_elem.text if title_elem is not None else ""
                    
                    link_elem = item.find('link')
                    url = link_elem.text if link_elem is not None else ""
                    
                    date_elem = item.find('pubDate')
                    date_str = date_elem.text if date_elem is not None else ""
                    
                    desc_elem = item.find('description')
                    description = desc_elem.text if desc_elem is not None else ""

                title = title.strip()
                url = url.strip() if url else ""
                
                # Cleanup HTML in description
                if description:
                    # Strip HTML tags
                    description = re.sub(r'<[^>]*>', '', description)
                    description = description.replace('&nbsp;', ' ').strip()
                    # Limit length
                    if len(description) > 300:
                        description = description[:297] + "..."

                if not title or not url:
                    continue

                # Parse publish date
                if not date_str:
                    continue
                try:
                    pub_date = parsedate_to_datetime(date_str)
                    # Convert to timezone aware UTC
                    if pub_date.tzinfo is None:
                        pub_date = pub_date.replace(tzinfo=timezone.utc)
                    else:
                        pub_date = pub_date.astimezone(timezone.utc)
                except Exception as de:
                    print(f"  Skipping article due to invalid pubdate format '{date_str}': {de}")
                    continue

                # Exclude if older than cutoff date
                if pub_date < cutoff_date:
                    continue

                # Increment processed candidate count
                global STATS_TOTAL_RSS, STATS_MATCHING_GTA6, STATS_DISCARDED
                STATS_TOTAL_RSS += 1

                # Filter GTA 6 articles
                if not is_gta6_relevant(title, description, feed_info["id"], url):
                    STATS_DISCARDED += 1
                    continue
                
                STATS_MATCHING_GTA6 += 1

                # Find Image URL
                image_url = find_image(item, url)

                article = {
                    "id": generate_id(title, url),
                    "title": title,
                    "source": feed_info["name"],
                    "sourceId": feed_info["id"],
                    "category": classify_article(title, description, feed_info["category"]),
                    # "Z" rather than isoformat()'s "+00:00": the app parses these with
                    # java.time.Instant.parse, which rejects numeric offsets below API 31
                    # and silently degraded every timestamp to "Recently".
                    "publishedAt": pub_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    "description": description,
                    "image": image_url,
                    "url": url,
                    # Populates SpeculativeArticleDto.confidence, which the DTO already
                    # declared but nothing ever set.
                    "confidence": feed_info.get("tier", "medium")
                }
                articles.append(article)
            except Exception as item_error:
                print(f"  Failed parsing item in {feed_info['name']}: {item_error}")
                continue
                
    except Exception as e:
        print(f"  Error fetching/parsing feed {feed_info['name']}: {e}")
        
    print(f"  Parsed {len(articles)} matching articles from {feed_info['name']}.")
    return articles

def load_existing_feed():
    if os.path.exists(FEED_FILE_PATH):
        try:
            with open(FEED_FILE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict) and "articles" in data:
                    return data["articles"]
                elif isinstance(data, list):
                    return data
        except Exception as e:
            print(f"Error loading existing feed: {e}")
    return []

def save_feed(articles):
    # Ensure directory exists
    os.makedirs(os.path.dirname(FEED_FILE_PATH), exist_ok=True)
    
    feed_data = {
        "lastUpdated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "articleCount": len(articles),
        "articles": articles
    }
    
    with open(FEED_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(feed_data, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(articles)} articles to {FEED_FILE_PATH}.")

CURATED_LEAKS_PATH = os.path.join("pipeline", "curated_leaks.json")


def load_curated_leaks():
    if not os.path.exists(CURATED_LEAKS_PATH):
        return []
    try:
        with open(CURATED_LEAKS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("articles", [])
    except Exception as e:
        print(f"Error loading curated leaks: {e}")
        return []

def merge_and_deduplicate(existing, fetched, curated):
    """
    Curated and seed entries used to be exempt from the age cutoff, so they never
    expired — which is why the live feed still led with GTAForums posts from 2023.
    Everything now obeys MAX_AGE_DAYS, curated included.
    """
    merged = []

    # 1. Process all fetched articles
    for article in fetched:
        dup = False
        for existing_m in merged:
            if is_duplicate(article, existing_m):
                dup = True
                break
        if not dup:
            merged.append(article)

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=MAX_AGE_DAYS)

    def within_age(article):
        try:
            return datetime.fromisoformat(article["publishedAt"]) >= cutoff_date
        except Exception:
            return False  # unparseable date -> discard

    # 2. Curated leaks, subject to the same age cutoff as everything else
    for article in curated:
        if not within_age(article):
            continue
        dup = False
        for existing_m in merged:
            if is_duplicate(article, existing_m):
                dup = True
                break
        if not dup:
            merged.append(article)

    # 3. Previously published articles, re-checked against the current rules
    for article in existing:
        if not within_age(article):
            continue
        if not is_gta6_relevant(
            article["title"], article.get("description", ""),
            article.get("sourceId", ""), article.get("url", "")
        ):
            continue

        dup = False
        for existing_m in merged:
            if is_duplicate(article, existing_m):
                dup = True
                break
        if not dup:
            merged.append(article)

    # 4. Sort by publish date descending
    def get_pubdate(a):
        try:
            return datetime.fromisoformat(a["publishedAt"].replace("Z", "+00:00"))
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)

    merged.sort(key=get_pubdate, reverse=True)

    # 5. Cap how much of the feed any single outlet can occupy.
    #
    # The highest-volume source publishes several GTA 6 posts a day, so straight
    # date ordering filled the top of the feed with one outlet and buried everyone
    # else. Overflow is kept in order and used only if there is room left.
    per_source = {}
    primary, overflow = [], []
    for article in merged:
        sid = article.get("sourceId", "")
        per_source[sid] = per_source.get(sid, 0) + 1
        (primary if per_source[sid] <= MAX_PER_SOURCE else overflow).append(article)

    result = primary[:MAX_ARTICLES]
    if len(result) < MAX_ARTICLES:
        result.extend(overflow[:MAX_ARTICLES - len(result)])
        result.sort(key=get_pubdate, reverse=True)

    return result

def main():
    existing_articles = load_existing_feed()
    print(f"Loaded {len(existing_articles)} existing articles.")
    
    curated_articles = load_curated_leaks()
    print(f"Loaded {len(curated_articles)} curated leaks.")
    
    newly_fetched = []
    for feed in FEEDS:
        newly_fetched.extend(parse_rss_feed(feed))
        
    print(f"Fetched {len(newly_fetched)} new candidates in total.")
    print(f"Total valid RSS articles processed: {STATS_TOTAL_RSS}")
    print(f"Articles matching GTA 6: {STATS_MATCHING_GTA6}")
    print(f"Articles discarded: {STATS_DISCARDED}")
    
    updated_articles = merge_and_deduplicate(existing_articles, newly_fetched, curated_articles)
    print(f"Final article count in feed: {len(updated_articles)}")
    save_feed(updated_articles)

if __name__ == "__main__":
    main()
