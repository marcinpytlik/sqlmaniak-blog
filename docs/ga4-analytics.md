# GA4 — SQLManiak Blog

GA4 Measurement ID: `G-LBVBW10S49` (publiczny identyfikator, w `hugo.toml`).

## Zachowanie zgody
- Bez decyzji: widoczny baner; **żaden skrypt Google nie jest pobierany**.
- Odrzucenie: decyzja zapisana lokalnie; żadnego Google Analytics.
- Akceptacja: asynchronicznie ładowany `gtag.js`, a następnie GA4.
- Zmiana decyzji: przycisk „Ustawienia analityki” w stopce; cofnięcie zgody odświeża kartę, żeby zakończyć dalsze pomiary.
- Gdy pamięć localStorage jest niedostępna, decyzja działa tylko do odświeżenia karty; kolejna wizyta ponownie zapyta o zgodę.

## Pomiar
- GA4 Enhanced Measurement: odsłony, scroll, outbound links (konfiguracja w interfejsie GA4).
- Własne zdarzenia: `contact_click`, `offer_click`, `easytools_click`; tylko po akceptacji.
- Kliknięcie `/oferta/` z bloga jest inne niż odsłona strony `/oferta/`; raportować je osobno.
- W GA4 sprawdzić Realtime/DebugView i w razie potrzeby oznaczyć zdarzenia jako kluczowe.
- W linkach LinkedIn używać UTM, np. `?utm_source=linkedin&utm_medium=social&utm_campaign=sqlquiz`.

## Kontrola przed połączeniem z master
1. `hugo --minify` oraz porównanie wyniku builda.
2. DevTools → Network: przed zgodą **zero zapytań** do `googletagmanager.com` / `google-analytics.com`.
3. Odrzuć → przejdź na inną podstronę → brak tagów GA.
4. Zaakceptuj → pojawia się `gtag/js?id=G-LBVBW10S49`; zweryfikuj GA4 Realtime.
5. Wycofaj zgodę ze stopki → strona się przeładowuje; nowe zapytania GA nie powinny być wysyłane.
6. Sprawdź zdarzenia kliknięć w ofertę, kontakt i Easytools (jeśli link występuje).
7. Sprawdź telefon, klawiaturę i jasny/ciemny motyw.
8. Uzupełnij politykę prywatności i informacje o administratorze/GA4 przed wdrożeniem; mechanizm zgody i tekst trzeba zweryfikować prawnie dla własnego serwisu.

Uwaga: mechanizm opiera się na skrypcie klienta. Rozszerzenia blokujące reklamy i AdGuard DNS mogą blokować endpointy Google nawet po wyrażeniu zgody. Aby przetestować dane, użyj przeglądarki bez aktywnej blokady dla domen Google Analytics.
