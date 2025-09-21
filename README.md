
# SQL Maniak — blog (Hugo + GitHub Pages)

Darmowy starter bloga oparty o **Hugo** i publikowany na **GitHub Pages**. Piszesz posty w Markdown (`content/posts/*.md`), a GitHub Actions automatycznie buduje i publikuje stronę.

## Szybki start (lokalnie)

1. Zainstaluj **Hugo Extended**: https://gohugo.io/installation/
2. Sklonuj repo i wejdź do katalogu:
   ```bash
   git clone https://github.com/<twoj-user>/sqlmaniak-blog.git
   cd sqlmaniak-blog
   ```
3. Uruchom podgląd:
   ```bash
   hugo server -D
   ```
   Otwórz przeglądarkę: http://localhost:1313

> VS Code: w `Terminal → Run Task` masz zadanie **Hugo: dev server**.

## Publikacja na GitHub Pages

1. Utwórz nowe repo `sqlmaniak-blog` w swoim GitHubie.
2. Skopiuj zawartość tego folderu i wypchnij na gałąź `main`.
3. Workflow `.github/workflows/deploy.yml`:
   - buduje stronę (Hugo)
   - publikuje na **GitHub Pages** (gałąź `gh-pages` zarządzana przez Pages artifact)
4. Wejdź w `Settings → Pages` i potwierdź, że **Source: GitHub Actions**.

Gotowe. Strona będzie widoczna pod adresem:  
`https://<twoj-user>.github.io/` (lub pod Twoją domeną).

## Własna domena (np. `sqlmaniak.blog`)

- Edytuj plik `static/CNAME` i wpisz tam **dokładny** adres domeny (np. `sqlmaniak.blog`).
- W panelu DNS ustaw rekord **CNAME**:  
  `sqlmaniak.blog → <twoj-user>.github.io`
- Przepchnij zmiany do `main`. Przy następnym deployu Pages utworzy CNAME.

> Jeśli nie masz jeszcze domeny — usuń plik `static/CNAME` lub zostaw pusty.

## Dodawanie postów

```bash
hugo new posts/2025-09-21-wpis.md
# Edytuj plik w content/posts/...
# Potem commit+push → GitHub Pages zdeployuje nową wersję
```

Front matter (na górze pliku) wspiera tagi, kategorie, opis i datę.

## Struktura

```
sqlmaniak-blog/
├─ archetypes/        # szablony nowych postów
├─ content/posts/     # Twoje artykuły
├─ static/            # statyczne pliki (CSS, obrazy, CNAME)
├─ themes/sqlmaniak/  # minimalny wbudowany motyw
├─ .github/workflows/ # GitHub Actions (deploy)
├─ .vscode/           # zadania VS Code
└─ hugo.toml          # konfiguracja
```

## SEO i analityka

- Ustaw `baseURL` w `hugo.toml` (np. `https://sqlmaniak.blog/`).
- Dodaj Google Analytics 4 (opcjonalnie) — można dodać w nadpisanej partialce albo osadzić skrypt w `baseof.html`.

## Licencja

Creative Commons BY 4.0 — możesz używać i modyfikować, podając autora.
