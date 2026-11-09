# Multilingual SQLManiak blog

## Language rollout
- Polish (PL): original and default language; public URLs stay unchanged.
- English (EN): enabled under `/en/`.
- German (DE): enabled under `/de/`.
- Portuguese (PT): only if justified by audience interest.

## Translation workflow
1. Keep existing Polish Markdown files in place.
2. To translate `content/posts/example.md`, create `content/posts/example.en.md` and/or `content/posts/example.de.md`. The shared basename links the translations in Hugo.
3. Translate title, description, prose, headings and tags; check SQL and technical terminology against the source. Never silently change benchmark data or code.
4. Localized `slug` values create language-specific URLs under `/en/posts/` and `/de/posts/`, while the original Polish slug is unchanged.
5. The language switcher points to a real translation when available and otherwise points to the selected language homepage.
6. Never create alternate-language `hreflang` entries for non-existent translations.
7. Run `hugo --minify --printI18nWarnings` and check all three URLs before merging.

## Navigation
The English and German navigation includes translated About, Contact and Services pages, in addition to Home, Posts, tags/categories, RSS and YouTube. Polish-only scripts and publications are not falsely presented as translated. The EN/DE Services pages are concise catalog overviews grounded in the original Polish offer, not full translations of its detailed training descriptions. The Polish privacy notice is explicitly identified as Polish and requires organizational/legal review before translated legal notices are published. See `docs/privacy-review-before-translations.md`. The Polish privacy notice is linked explicitly as Polish in the footer.

## SEO and analytics
Each page has a self-referential canonical URL. Alternate `hreflang` links are emitted only for real translation counterparts. Hugo generates language-specific feeds and sitemap entries. Existing GA4 consent handling is shared; UI copy is localized.

## Information pages
The build validates all PL/EN/DE About, Contact and Services pages, canonical/hreflang links and the unmodified Formspree endpoint using `scripts/verify_info_pages.py`. The endpoint remains unchanged, but delivery to the mailbox must be verified with a real form submission by the site owner.

## Deployment
Open a pull request from the feature branch into `master`. The validation workflow verifies all three languages and Polish URL continuity. Review and merge after the checks pass. The existing GitHub Pages deployment runs on merge.
