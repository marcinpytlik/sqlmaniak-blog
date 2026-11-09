#!/usr/bin/env python3
"""Validate localized About, Contact, Services navigation and form contract."""
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path("public")
LANG = {
    "pl": {"about": "/about/", "contact": "/contact/", "offer": "/oferta/"},
    "en": {"about": "/en/about/", "contact": "/en/contact/", "offer": "/en/services/"},
    "de": {"about": "/de/about/", "contact": "/de/contact/", "offer": "/de/leistungen/"},
}
ACTION = "https://formspree.io/f/mzzjpewn"

class Inspector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.hrefs = []
        self.alternates = {}
        self.canonicals = []
        self.h1_count = 0
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a":
            self.hrefs.append(a.get("href", ""))
        if tag == "h1":
            self.h1_count += 1
        if tag == "form":
            self.tags.append(("form", a))
        if tag in ("input", "textarea"):
            self.tags.append((tag, a))
        if tag == "link" and a.get("rel") == "canonical":
            self.canonicals.append(a.get("href"))
        if tag == "link" and a.get("rel") == "alternate" and a.get("hreflang"):
            self.alternates[a.get("hreflang")] = a.get("href")

def check(condition, message):
    if not condition:
        raise SystemExit("INFO PAGES CHECK FAILED: " + message)

def inspect(path):
    file = ROOT / path.lstrip("/") / "index.html"
    check(file.is_file(), "Missing page " + str(file))
    p = Inspector()
    p.feed(file.read_text(encoding="utf-8"))
    return p

for lang, paths in LANG.items():
    home = inspect("/" if lang == "pl" else "/" + lang + "/")
    for path in paths.values():
        check(path in home.hrefs, f"{lang} homepage navigation missing {path}")
    for key, path in paths.items():
        p = inspect(path)
        check(p.h1_count == 1, f"{lang}/{key} expected one H1, got {p.h1_count}")
        url = "https://sqlmaniak.blog" + path
        check(p.canonicals == [url], f"{lang}/{key} wrong canonical {p.canonicals}")
        for target_lang, target_paths in LANG.items():
            target = "https://sqlmaniak.blog" + target_paths[key]
            check(p.alternates.get(target_lang) == target, f"{lang}/{key}: bad {target_lang} hreflang")
        check(p.alternates.get("x-default") == "https://sqlmaniak.blog" + LANG["pl"][key], f"{lang}/{key}: wrong x-default")
        if key == "contact":
            forms = [a for tag, a in p.tags if tag == "form"]
            check(len(forms) == 1, f"{lang} should have one contact form")
            check(forms[0].get("action") == ACTION and forms[0].get("method","").lower() == "post", f"{lang}: form endpoint/method changed")
            fields = {a.get("name"): a for tag, a in p.tags if tag in ("input", "textarea")}
            for required in ("name", "_replyto", "message"):
                check(required in fields and "required" in fields[required], f"{lang}: missing required {required}")
            check("_gotcha" in fields and "_subject" in fields, f"{lang}: hidden form metadata missing")
        print(f"PASS {lang}/{key}: route, canonical, hreflang, H1" + (", form" if key == "contact" else ""))
print("All international information page checks passed.")
