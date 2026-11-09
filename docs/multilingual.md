# Multilingual SQLManiak blog

## Language rollout
- Polish (PL): original and default language; public URLs stay unchanged.
- English (EN): enabled under `/en/`.
- German (DE): next stage, not enabled yet.
- Portuguese (PT): only if justified by audience interest.

## Translation workflow
1. Keep existing Polish Markdown files in place.
2. To translate `content/posts/example.md`, create `content/posts/example.en.md`. The shared basename links the translations in Hugo.
3. Translate title, description, prose, headings and tags; check SQL and technical terminology against the source. Never silently change benchmark data or code.
4. An English `slug` creates an English URL under `/en/posts/`, while the original Polish slug is unchanged.
5. The language switcher points to a real translation when available and otherwise points to the selected language homepage.
6. Never create alternate-language `hreflang` entries for non-existent translations.
7. Run `hugo --minify --printI18nWarnings` and check both URLs before merging.

## Navigation
The English navigation deliberately includes only pages with an English-language destination (Home, Posts, tags/categories, RSS, YouTube). Polish-only offer, about, contact, scripts and publications are not falsely presented as English. The Polish privacy notice is linked explicitly as Polish in the footer.

## SEO and analytics
Each page has a self-referential canonical URL. Alternate `hreflang` links are emitted only for real translation counterparts. Hugo generates language-specific feeds and sitemap entries. Existing GA4 consent handling is shared; UI copy is localized.

## Deployment
Open a pull request from the feature branch into `master`. The validation workflow verifies both languages and Polish URL continuity. Review and merge after the checks pass. The existing GitHub Pages deployment runs on merge.
