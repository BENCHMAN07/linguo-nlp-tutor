"""Respectful cached crawler for the SRM Computational Linguistics course site."""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

ROOT = "https://lectures.rebeccakennet.com/21cse552t-computational-linguistics/"
BASE = "https://lectures.rebeccakennet.com"
DATA = Path(__file__).resolve().parents[1] / "data"
RAW = DATA / "raw"
UA = "LinguoAcademicPrototype/1.0 (personal learning project; respectful crawl)"
EXPECTED = {1: 6, 2: 8, 3: 8, 4: 9, 5: 7}
UNIT_TITLES = {1: "Introduction", 2: "Overview of Grammar", 3: "Products of Computational Linguistics",
               4: "Language as a Meaning to Text Transformer", 5: "Linguistic Models"}


def slug(url: str) -> str:
    path = re.sub(r"[^a-zA-Z0-9_-]+", "_", urlparse(url).path.strip("/"))
    return (path or "course") + ".html"


def allowed(session: requests.Session, url: str) -> bool:
    robots_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}/robots.txt"
    path = RAW / "robots.txt"
    if path.exists():
        body = path.read_text(encoding="utf-8", errors="replace")
    else:
        response = session.get(robots_url, timeout=20)
        # RFC 9309 treats an unavailable robots resource (including 404) as
        # no rules. Server errors remain closed by failing the crawl safely.
        if response.status_code >= 500:
            response.raise_for_status()
        body = "" if response.status_code == 404 else response.text
        path.write_text(body, encoding="utf-8")
    parser = RobotFileParser()
    parser.parse(body.splitlines())
    return parser.can_fetch(UA, url)


def fetch(session: requests.Session, url: str, failures: list[dict]) -> str | None:
    path = RAW / slug(url)
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace")
    try:
        is_allowed = allowed(session, url)
    except requests.RequestException as exc:
        failures.append({"url": url, "error": f"Could not read robots.txt: {exc}"})
        return None
    if not is_allowed:
        failures.append({"url": url, "error": "Disallowed by robots.txt"})
        return None
    time.sleep(1)
    try:
        response = session.get(url, timeout=25)
        response.raise_for_status()
        if "html" not in response.headers.get("content-type", "").lower():
            failures.append({"url": url, "error": "Response was not HTML"})
            return None
        body = response.content.decode("utf-8", errors="replace")
        path.write_text(body, encoding="utf-8")
        return body
    except requests.RequestException as exc:
        failures.append({"url": url, "error": str(exc)})
        return None


def clean_text(node) -> str:
    return " ".join(node.stripped_strings)


def extract(url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    title = clean_text(soup.title) if soup.title else ""
    main = soup.find("main") or soup.find("article") or soup.body or soup
    sections = []
    heading = "Overview"
    parts = []
    for element in main.find_all(["h1", "h2", "h3", "h4", "p", "ul", "ol", "table", "pre", "img"], recursive=True):
        if element.name in ("h1", "h2", "h3", "h4"):
            if parts:
                sections.append({"heading": heading, "text": "\n".join(parts)})
            heading = clean_text(element)
            parts = []
        elif element.name in ("ul", "ol"):
            parts.append("\n".join("• " + clean_text(li) for li in element.find_all("li", recursive=False)))
        elif element.name == "table":
            parts.append("\n".join(" | ".join(clean_text(c) for c in row.find_all(["th", "td"], recursive=False)) for row in element.find_all("tr")))
        elif element.name == "img":
            if element.get("alt"):
                parts.append("Image: " + element["alt"])
        else:
            parts.append(clean_text(element))
    if parts:
        sections.append({"heading": heading, "text": "\n".join(parts)})
    links = [{"text": clean_text(a), "url": urljoin(url, a.get("href", ""))}
             for a in main.find_all("a", href=True) if urlparse(urljoin(url, a["href"])).netloc == urlparse(BASE).netloc]
    resources = [{"text": clean_text(a), "url": urljoin(url, a.get("href", ""))}
                 for a in main.find_all("a", href=True)
                 if re.search(r"\.(pdf|pptx?|docx?)(?:$|\?)|slides\.google\.com|docs\.google\.com", urljoin(url, a["href"]), re.I)]
    return {"title": title, "sections": sections, "links": links, "resources": resources}


def rendered_links() -> tuple[list[tuple[str, int]], dict[str, str], str | None]:
    """Hydrate the JS course page and expand each unit accordion when needed."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return [], {}, "Playwright is not installed"
    discovered: list[tuple[str, int]] = []
    rendered: dict[str, str] = {}
    error = None
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(user_agent=UA)
            page.goto(ROOT, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(1200)
            for unit in range(1, 6):
                button = page.locator(f"#unit-{unit} button").first
                if button.count():
                    button.click()
                    page.wait_for_timeout(350)
            rendered[ROOT] = page.content()
            for unit in range(1, 6):
                section = page.locator(f"#unit-{unit}")
                links = section.locator("a[href]").evaluate_all("els => els.map(a => ({href:a.href,text:(a.innerText||'').trim()}))")
                for link in links:
                    url = link["href"].split("#", 1)[0]
                    if url.startswith(ROOT) and url.rstrip("/") != ROOT.rstrip("/"):
                        discovered.append((url, unit))
            browser.close()
    except Exception as exc:
        print(f"Playwright fallback failed: {exc}")
        error = str(exc)
    return discovered, rendered, error


def main() -> None:
    DATA.mkdir(exist_ok=True)
    RAW.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": UA})
    failures: list[dict] = []
    pages: dict[str, dict] = {}
    for url in (ROOT, urljoin(ROOT, "syllabus/"), urljoin(ROOT, "exam-prep/")):
        html = fetch(session, url, failures)
        if html:
            pages[url] = extract(url, html)

    course = pages.get(ROOT, {"links": []})
    excluded = {urljoin(ROOT, "syllabus/"), urljoin(ROOT, "exam-prep/")}
    link_cache = RAW / "discovered_links.json"
    queue: list[tuple[str, int]] = []
    if link_cache.exists():
        queue = [(row["url"], row["unit"]) for row in json.loads(link_cache.read_text(encoding="utf-8"))]
    else:
        # Recover links from a completed raw cache if this is an upgrade from
        # an earlier scraper run. This avoids opening the live site again.
        unit_dirs = {"introduction": 1, "overview-of-grammar": 2,
                     "products-of-computational-linguistics": 3, "language-as-a-meaning": 4,
                     "linguistic-models": 5}
        root_slug = slug(ROOT)[:-5]
        for cached in RAW.glob("*.html"):
            stem = cached.stem
            prefix = root_slug + "_"
            if not stem.startswith(prefix):
                continue
            relative = stem[len(prefix):]
            url = ROOT + relative.replace("_", "/") + "/"
            unit = unit_dirs.get(relative.split("_", 1)[0], 0)
            if unit and url not in excluded:
                queue.append((url, unit))
        if not queue:
            for link in course["links"]:
                match = re.search(r"unit\s*([1-5])", link["text"] + " " + link["url"], re.I)
                if match:
                    queue.append((link["url"], int(match.group(1))))
                elif link["url"].startswith(ROOT) and link["url"] not in excluded:
                    queue.append((link["url"], 0))
    if not queue:
        dynamic_links, dynamic_pages, dynamic_error = rendered_links()
        queue.extend(dynamic_links)
        pages.update({url: extract(url, html) for url, html in dynamic_pages.items()})
        if dynamic_error:
            failures.append({"url": ROOT, "error": f"Playwright lecture-link discovery failed: {dynamic_error}"})
        elif not dynamic_links:
            failures.append({"url": ROOT, "error": "No lecture links were found in the static or rendered course page"})
    unit_for_page: dict[str, int] = {}
    seen: set[str] = set()
    while queue and len(seen) < 50:
        url, parent_unit = queue.pop(0)
        if url in seen or url in excluded or not url.startswith(ROOT):
            continue
        seen.add(url)
        unit_match = re.search(r"unit[-_/ ]?([1-5])", url, re.I)
        unit = int(unit_match.group(1)) if unit_match else parent_unit
        unit_for_page[url] = unit
        html = fetch(session, url, failures)
        if not html:
            continue
        page = extract(url, html)
        pages[url] = page
        for link in page["links"]:
            target = link["url"].split("#", 1)[0]
            if target.startswith(ROOT) and target not in excluded and target not in seen:
                link_unit = re.search(r"unit\s*([1-5])", link["text"] + " " + target, re.I)
                queue.append((target, int(link_unit.group(1)) if link_unit else unit))
    if seen:
        link_cache.write_text(json.dumps([{"url": url, "unit": unit_for_page.get(url, 0)} for url in sorted(seen)], indent=2), encoding="utf-8")
    lectures = []
    unit_counts = {i: 0 for i in range(1, 6)}
    for url, page in pages.items():
        if url in (ROOT, urljoin(ROOT, "syllabus/"), urljoin(ROOT, "exam-prep/")):
            continue
        match = re.search(r"unit[-_/ ]?([1-5])", url + " " + page["title"], re.I)
        unit = int(match.group(1)) if match else unit_for_page.get(url, 0)
        if not unit:
            continue
        # A unit overview is not itself a lecture. Retain only pages with body text
        # and a lecture-like title or numbered URL, never manufacture placeholders.
        path_parts = urlparse(url).path.rstrip("/").split("/")
        if path_parts[-1].lower() in {"notes", "present", "presentation", "slides"}:
            continue
        if re.search(r"unit\s*[1-5]", page["title"], re.I) and not re.search(r"lecture|class|lesson", page["title"], re.I):
            continue
        unit_counts[unit] += 1
        text = " ".join(section["text"] for section in page["sections"])
        terms = sorted(set(re.findall(r"\b[A-Z][a-zA-Z-]{3,}\b", text)))
        related = [purl for purl in pages if purl.startswith(url.rstrip("/") + "/") and urlparse(purl).path.rstrip("/").split("/")[-1].lower() in {"notes", "present", "presentation", "slides"}]
        lectures.append({"unit": unit, "unit_title": UNIT_TITLES[unit], "lecture_id": f"u{unit}-l{unit_counts[unit]}",
                         "title": page["title"], "url": url, "sections": page["sections"],
                         "key_terms": terms, "source_url": url,
                         "resources": ([{"text": "Lecture notes or slides", "url": purl} for purl in related] +
                                       page.get("resources", []))})
    (DATA / "lectures.json").write_text(json.dumps(lectures, indent=2), encoding="utf-8")
    (DATA / "syllabus.json").write_text(json.dumps(pages.get(urljoin(ROOT, "syllabus/"), {}), indent=2), encoding="utf-8")
    (DATA / "exam_prep.json").write_text(json.dumps(pages.get(urljoin(ROOT, "exam-prep/"), {}), indent=2), encoding="utf-8")
    report = {"pages_fetched_or_cached": len(pages), "lectures_per_unit": unit_counts,
              "expected_per_unit": EXPECTED,
              "missing_lectures_per_unit": {str(u): max(0, EXPECTED[u]-unit_counts[u]) for u in EXPECTED},
              "failures": failures}
    (DATA / "scrape_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
