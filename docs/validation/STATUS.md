# Stan walidacji i co zostało

Stan na 19 sierpnia 2026.

**Ślad audytowy walidacji nie jest w repozytorium.** Sprawdzenie zostawiło 618 plików
z zapisem każdej pojedynczej decyzji — wersją sprzed zmiany, uzasadnieniem i dowodem.
Pola `evidence` cytują podręcznik dosłownie, wraz z numerami stron, a repozytorium jest
publiczne, więc katalog `docs/validation/` jest w `.gitignore` z wyjątkiem tego pliku
i `DECISIONS.md`. Zapis leży u autora poprawek i jest do wglądu na życzenie — pozwala
odtworzyć, skąd wzięła się każda z 948 zmian. Pełna historia gita sprzed usunięcia
katalogu została zachowana lokalnie i nie jest wypychana.

## Zrobione

3389 pytań z `data/neuro_questions.xlsx` sprawdzonych względem podręcznika Krasuckiego
trzema niezależnymi metodami: walidator czytający transkrypcję z kluczem przed oczami,
solver rozwiązujący na ślepo bez klucza, rozjemca czytający oryginalny skan przy sporach.

| | |
|---|---|
| poprawionych kluczy odpowiedzi | 228 |
| poprawionych lub przepisanych wyjaśnień | 497 |
| poprawek treści pytań i opcji | 34 |
| usterek technicznych | 6 |
| przenumerowanych ID | 150 |
| wykluczonych pytań | 34 |
| **zmian w dzienniku `applied-changes.json`** | **948** |
| pytań w quizie | 3389 → **3355** |

Każda zmiana ma w dzienniku wartość sprzed, uzasadnienie i źródło sygnału.

## Zostało — nic z tego nie jest pilne

**Przekazanie poprawek do repozytorium źródłowego.** Projekt Lovable synchronizuje się
z `agatajustyna/neuro-wiry-hub`, więc na stronę poprawki trafią dopiero po scaleniu pull
requesta tam. Praca powstała w forku `adamdrzewiecki/neuro-wiry-hub`.

**334 ubogie wyjaśnienia** — poprawne merytorycznie, ale nietłumaczące, dlaczego pozostałe
opcje są błędne. Rozsypane po działach: Mózgowie i rdzeń 103, Międzymózgowie 95,
Rdzeń kręgowy 66, Nerwy czaszkowe 23, reszta pojedynczo. Świadomie zostawione — decyzja
właściciela zbioru brzmiała „zrób Kresomózgowie i na tym się zatrzymaj". Procedura
wznowienia: `scripts/validation/prepare_enrich.py <dział>` plus przebieg wzbogacający.

**Jedna pozycja nierozstrzygnięta** — `2.Opony mózgowo-rdzeniowe` w.27, zakończenie stożka
opony twardej. Szczegóły w [DECISIONS.md](DECISIONS.md).

**Kompletność wyjaśnień poza wybranymi działami** — 2858 nietkniętych wyjaśnień ma medianę
203 znaków wobec 419 w tych pisanych przez nas. To nie są błędy.

## Uruchomienie aplikacji

Brak skilla projektowego; warto go dodać przez `/run-skill-generator`. Do tego czasu:

- `npm run dev` słucha na **porcie 8080**, nie na typowym 5173.
- Wejście prosto na `/quiz?sections=[N]&count=M` **nie ładuje puli** — trzeba przejść przez
  stronę startową: kliknąć dział (to przyciski-pigułki, nie checkboxy), wybrać liczbę pytań,
  kliknąć „Rozpocznij test".
- Na ekranie quizu **pierwsze trzy przyciski to regulacja rozmiaru czcionki**; odpowiedzi
  zaczynają się od indeksu 3.
- `chromium-cli` niedostępne; sterowanie przez Playwrighta (`npx playwright install chromium`),
  uruchamianego z katalogu, w którym Playwright jest zainstalowany.

## Czego nauczyła ta sesja

**Nie każ agentom masowo czytać stron skanu.** Pierwsze podejście spaliło 63,6 mln tokenów
na jednej trzeciej zbioru i nie dało ani jednej zweryfikowanej poprawki. Praca na transkrypcji
kosztuje ok. 2,4 tys. tokenów na pytanie, na obrazie skanu ok. 11,6 tys. Skan tylko do
rozstrzygania sporów i zawsze grupowany po stronach.

**Dossier per pytanie zamiast per temat.** Przy 33 pytaniach rozrzuconych po 27 tematach
dossier tematyczne dały 1508 KB źródła do wczytania, a dobrane pod konkretne pytania 355 KB.

**Dwa niezależne sygnały przed zmianą klucza.** Z 82 spornych przypadków połowa okazała się
fałszywym alarmem. Walidator widzący klucz i solver rozwiązujący na ślepo mylą się w innych
miejscach.

**Sprawdzaj przesunięcie wierszy.** Agent potrafi odpowiedzieć poprawnie, ale przypisać
odpowiedzi do sąsiednich wierszy — zdarzyło się w `4.Kora mózgu - Wyspa` i wyglądało jak
18 błędów klucza. Test: policz zgodność przy przesunięciu o ±1.

**Poprawka opcji unieważnia wyjaśnienie.** Po każdej zmianie treści pola sprawdź, czy
wyjaśnienie nie broni usuniętej treści. Złapało to m.in. wyjaśnienie mówiące „Istota czarna
leży w nakrywce śródmózgowia" przy opcji zmienionej na torebkę wewnętrzną.

**Detektory leksykalne zawodzą po polsku.** Pomiar „czy wyjaśnienie odnosi się do opcji X"
przez dopasowanie słów dał trzy fale fałszywych alarmów: odmiana („sznurze bocznym" wobec
„sznura bocznego") i parafraza („szybkiego przewodzenia" wobec „przewodzenie skokowe
przyspiesza transmisję"). Stemmer pomaga tylko na odmianę. Ufaj miarom obiektywnym:
długość, liczba zdań, obecność odwołań do liter, nienaruszalność klucza.

**Wartość domyślna gorsza niż twardy błąd.** Parametr `args` dotarł do skryptu przebiegu jako
string, `args.section` było undefined, zadziałał fallback i cały przebieg powtórzył wykonaną
już pracę — 7,8 mln tokenów. Gdyby skrypt przerwał pracę, kosztowałoby to zero.

**Agent zapisuje wynik na dysk, zanim go zwróci.** Przy trafieniu w limit wyniki z pamięci
przepadają, pliki zostają. Uratowało to 94 wyniki przy pierwszym trafieniu w limit.
