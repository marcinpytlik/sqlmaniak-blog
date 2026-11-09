#!/usr/bin/env python3
"""Build-time SEO regression checks for the two PL/EN/DE article families."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

ROOT = Path("public")
BASE = "https://sqlmaniak.blog"
FAMILIES = {
    "split": {
        "pl": "/posts/podzial-tabeli-bez-big-bang/",
        "en": "/en/posts/split-table-without-big-bang/",
        "de": "/de/posts/tabelle-aufteilen-ohne-big-bang/",
    },
    "merge": {
        "pl": "/posts/scalanie-tabel-bez-przestoju/",
        "en": "/en/posts/merging-tables-without-downtime/",
        "de": "/de/posts/tabellen-zusammenfuehren-ohne-ausfallzeit/",
    },
}

class PageInfo(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = []
        self.alternates = {}
        self.h1 = 0
        self.links = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "h1":
            self.h1 += 1
        if tag == "link" and a.get("rel") == "canonical":
            self.canonical.append(a.get("href"))
        if tag == "link" and a.get("rel") == "alternate" and a.get("hreflang"):
            self.alternates[a["hreflang"]] = a.get("href")
        if tag == "a":
            self.links.append(a.get("href", ""))

def fail(message):
    raise SystemExit("SEO CHECK FAILED: " + message)

def parse_page(path):
    file = ROOT / path.lstrip("/") / "index.html"
    if not file.is_file():
        fail(f"missing generated page {file}")
    parser = PageInfo()
    parser.feed(file.read_text(encoding="utf-8"))
    return parser

# Locate URLs across generated sitemap XMLs; Hugo may write one sitemap or a sitemap index.
urls = set()
xml_files = list(ROOT.rglob("sitemap*.xml"))
if not xml_files:
    fail("no generated sitemap XML")
for xml in xml_files:
    try:
        tree = ET.parse(xml)
    except ET.ParseError as exc:
        fail(f"invalid sitemap XML {xml}: {exc}")
    for node in tree.iter():
        if node.tag.rsplit("}", 1)[-1] == "loc" and node.text:
            urls.add(node.text.strip().rstrip("/"))

for label, translations in FAMILIES.items():
    expected = {lang: BASE + path for lang, path in translations.items()}
    for lang, path in translations.items():
        page = parse_page(path)
        url = expected[lang]
        if page.canonical != [url]:
            fail(f"{label}/{lang}: canonical should be {url}, got {page.canonical}")
        if page.h1 != 1:
            fail(f"{label}/{lang}: expected one H1; got {page.h1}")
        if url.rstrip("/") not in urls:
            fail(f"{label}/{lang}: URL missing in generated sitemap: {url}")
        for target_lang, target_url in expected.items():
            if page.alternates.get(target_lang) != target_url:
                fail(f"{label}/{lang}: wrong hreflang {target_lang}: {page.alternates}")
        if page.alternates.get("x-default") != expected["pl"]:
            fail(f"{label}/{lang}: wrong x-default")
        if len(page.alternates) != 4:
            fail(f"{label}/{lang}: unexpected alternate-language entries: {page.alternates}")
        print(f"PASS {label}/{lang}: URL, sitemap, canonical, hreflang, H1")

# The new merger articles must link to the existing table-splitting articles in the same language.
for lang in ("pl", "en", "de"):
    merger = parse_page(FAMILIES["merge"][lang])
    target = FAMILIES["split"][lang]
    if target not in merger.links:
        fail(f"merge/{lang}: related-article link missing: {target}")
    print(f"PASS merge/{lang}: related internal link")

print("All multilingual SEO checks passed.")
