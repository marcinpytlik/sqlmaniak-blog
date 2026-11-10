# SQLManiak PL / EN / DE — monitoring and acceptance plan

Status: monitoring plan, not proof of traffic, conversion or Google indexing.
Languages: Polish at `/`, English at `/en/`, German at `/de/`. No fourth language.

## 1. Production acceptance

- Confirm that `/about/`, `/contact/`, `/oferta/`, `/en/about/`, `/en/contact/`, `/en/services/`, `/de/about/`, `/de/contact/` and `/de/leistungen/` load correctly.
- Test the PL/EN/DE switcher from each translated page. Only genuine translation counterparts should be linked.
- Check responsive navigation, link to the original Polish privacy notice, and form accessibility on desktop and mobile.
- As site owner, submit one clearly labelled test message on EN and one on DE to Formspree. Confirm delivery to the target mailbox and delete test data according to retention practices. Static CI cannot prove delivery.
- Inspect `https://sqlmaniak.blog/sitemap.xml` and verify that the new pages appear in the generated sitemap. Do not confuse a valid sitemap with actual indexing.

## 2. GA4 event definitions

Measurement ID is configured in `hugo.toml`. The script `static/js/site-preferences.js` loads GA4 **only after opt-in**.

- `page_view`: supplied by Google after consent; use the `Page path + query string` dimension to distinguish `/`, `/en/`, `/de/`, and their articles. This metric is not a count of visitors.
- `contact_click`: click on a localized Contact page link, email or telephone link; **not** a submitted form or a validated lead.
- `offer_click`: click on the Polish offer or localized EN/DE Services pages; **not** a purchase.
- `easytools_click`: outbound clicks to supported Easytools domains (existing event).
- New event parameter `site_language` is `pl`, `en` or `de` according to the current page URL. Also pass `source_path`.

GA4 custom dimension: configure a **user-editable event-scoped** dimension named `Site language` with event parameter `site_language` in GA4 Admin → Custom definitions. That configuration is external to this repository and should be confirmed in the GA4 account.

For analysis, compare sessions, engaged sessions, article page views, average engagement, contact clicks and offer clicks per language. Segment by landing page, source/medium and country as appropriate. **Do not use country as a proxy for language.**

Consent-dependent data is incomplete by design. Do not compare all-site totals against language totals without documenting the filters and consent conditions. There is no backfill of events for past visits.

## 3. Google Search Console

Use the verified domain property (if available); inspect `Pages` / indexing and Search Results → Pages filtered by path prefixes. Track for each language:
- indexed URLs versus submitted URLs;
- impressions, clicks, CTR and average position over the **same dates** and with comparable page/query filters;
- canonical selected by Google for representative EN and DE pages;
- potential hreflang/crawl issues, when surfaced.

Use URL Inspection for a few representative articles and information pages. Request indexing only after the live URLs, canonical links and sitemap pass. Search Console trends can be delayed and low-volume data can be sparse.

## 4. Baseline and monitoring

Take an initial baseline after deployment. Continue weekly checks for 4–8 weeks with the same date windows, without extrapolating from 1–2 days. Keep the existing LinkedIn cadence. Report observations separately from hypotheses (e.g. changes in clicks cannot yet be attributed to new translations).

No account-side GA4, Search Console or Formspree configuration has been changed by the code PR. Those checks require access to the corresponding dashboards.

## 5. Privacy-document boundary

The current Polish policy contains an unresolved organizational/legal controller review in section 1 and factual statements about GA4 and Formspree retention. Before adding public EN/DE privacy pages:
- verify controller roles and factual processing arrangements;
- check actual platform settings, data retention and transfer notices;
- have the Polish text approved first, then translate and review the EN/DE notices.

See `docs/privacy-review-before-translations.md`. Do **not** claim the existing Polish policy has been finally approved.
