from pathlib import Path
import re

root = Path(__file__).resolve().parents[1]
config = (root / 'hugo.toml').read_text(encoding='utf-8')
template = (root / 'themes/sqlmaniak/layouts/_default/baseof.html').read_text(encoding='utf-8')
partial = (root / 'themes/sqlmaniak/layouts/partials/site-preferences.html').read_text(encoding='utf-8')
script = (root / 'static/js/site-preferences.js').read_text(encoding='utf-8')
css = (root / 'static/css/site-preferences.css').read_text(encoding='utf-8')

assert re.search(r'measurementID\s*=\s*"G-[A-Z0-9]+"', config), 'GA4 measurement ID missing'
assert '{{ partial "site-preferences.html" . }}' in template, 'Consent partial not included'
assert '/css/site-preferences.css' in template, 'Consent stylesheet missing'
assert 'site-pref-open' in template, 'Consent settings button missing'
assert 'data-site-preferences="accepted"' in partial
assert 'data-site-preferences="rejected"' in partial
assert '/js/site-preferences.js' in partial
assert 'getChoice() === "accepted"' in script or 'choice === "accepted"' in script
assert 'document.createElement("script")' in script, 'Google tag must be loaded dynamically'
assert 'google-analytics.com' not in template
assert 'googletagmanager.com' not in template
assert 'contact_click' in script and 'offer_click' in script and 'easytools_click' in script
assert '.site-preferences' in css
print('GA4 static integration checks passed. Browser consent tests still required.')

# Validate rendered site, not only template sources. A missing Hugo param silently skips the partial.
rendered = (root / 'public/index.html').read_text(encoding='utf-8')
assert 'site-pref-config' in rendered, 'GA4 config missing in generated HTML'
assert 'G-LBVBW10S49' in rendered, 'GA4 measurement ID not rendered'
assert 'site-pref-banner' in rendered, 'Consent banner not rendered'
assert '/js/site-preferences.js' in rendered, 'Consent script not rendered'
