# Zmiany: zakładka Publikacje

Dodano:

- `content/publications.md` — stała strona `/publikacje/`,
- link `Publikacje` w głównym menu,
- responsywne karty publikacji w arkuszu CSS,
- odnośniki do bezpłatnych fragmentów,
- odnośniki do zakupu pełnych wersji,
- alias `/publications/` przekierowujący na polską stronę.

Po skopiowaniu zmian wykonaj:

```powershell
git add content/publications.md themes/sqlmaniak/layouts/_default/baseof.html static/css/style.css themes/sqlmaniak/static/css/style.css CHANGES-PUBLIKACJE.md
git commit -m "Dodaj zakładkę Publikacje"
git push origin master
```
