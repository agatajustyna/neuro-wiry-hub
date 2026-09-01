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

## Stan po planie „detells" — 1 września 2026

Osobny plan (`docs/superpowers/plans/2026-08-30-neuro-quiz-detells.md`, gałąź `detells`) zajął się dwoma rodzajami usterek, których pierwsza walidacja nie mierzyła: dosłownymi odniesieniami do rycin książki („Image N") w wyjaśnieniach oraz wyróżnikami tekstowymi pozwalającymi zgadnąć poprawną odpowiedź bez wiedzy merytorycznej — długością, spójnikami, nawiasami, przecinkami i zwrotami kategorycznymi występującymi nierówno między poprawną opcją a dystraktorami. Instrument pomiarowy (`scripts/validation/measure_tells.py`) i walidujący applier (`scripts/validation/apply_field_changes.py`) powstały jako Task 1–2 tego planu; każda naniesiona zmiana ma wpis w `docs/validation/applied-changes.json` z polami `from`/`to`/`why`/`signals`, tak jak w pierwszej walidacji.

### Co zrobiono

| | Baseline | Po planie |
|---|---|---|
| odniesienia do rycin „Image" | 321 (141 nawiasowych, 180 wplecionych w zdanie) | **0** |
| nawias tylko-w-poprawnej | 359 | 8 (spadek do 9 zaraz po Tasku 5, dalszy dryf przy pracach nad długością) |
| zwroty kategoryczne w ≥2 dystraktorach | 99 | 3 (do 5 po Tasku 6, resztę domknęło rozjemstwo Tasku 7) |
| token „lub" tylko-w-poprawnej (mikro-runda domykająca) | 25 (ratio w `token_ratios` 25,0) | 6 (ratio 3,5) — patrz sekcja `token_ratios` niżej |
| unia wszystkich wyróżników | 1182 pytań (35,2%) | 74 pytań (2,2%) |

141 odniesień nawiasowych usunięto mechanicznie (skrypt, bez LLM), 180 wplecionych w zdanie przeredagowali agenci Sonnet z twardym zakazem zmiany treści merytorycznej i cytowania liter odpowiedzi. Nawiasy przeniesiono z poprawnej opcji do wyjaśnienia tam, gdzie było to możliwe bez utraty jednoznaczności (359 pytań, ślepy solver na próbce 40 potwierdził ≥95% trafień po edycji). Zwroty kategoryczne w dystraktorach złagodzono z równoległą weryfikacją błędności względem dossier źródłowego — ryzykiem było przypadkowe uczynienie dystraktora prawdziwym, dlatego część spornych przypadków (5 z 99) trafiła do rozjemstwa razem z balansem długości. Największy przebieg (balans długości/koniunkcji/przecinka) objął 849 pytań w głównej turze plus 91 w domykającej mini-turze dla samego wyróżnika „poprawna najdłuższa" — każda propozycja przeszła przez ślepego solvera i kontrolera błędności, spory rozjemcę na skanie oryginału. Z tych 91 kandydatów kontroler odrzucił 6 (chybienie ślepego solvera albo zastrzeżenie merytoryczne) i pozostawił je w stanie sprzed poprawki (`docs/validation/detells/dropped-mini.json`) — stąd 85, nie 91, w tabeli niżej.

Łącznie `docs/validation/applied-changes.json` urósł o **2559 wpisów** ponad 948 z pierwszej walidacji (log jest lokalny, poza gitem — patrz nota na początku pliku), obejmujące **1524 unikalnych pytań** (45,4% zbioru). Rozbicie wpisów per `signals` (policzone skryptem, granica dokładnie przy wpisie 948. — sygnatury sprzed tego indeksu pokrywają się co do liczby z tabelą z pierwszej walidacji):

| Task | Sygnał(y) w dzienniku | Wpisów | Unikalnych pytań |
|---|---|---|---|
| 3 — usunięcie nawiasowego „Image" | `mechaniczne usunięcie odniesienia do ryciny` | 141 | 141 |
| 4 — przeredagowanie wplecionego „Image" | `przeredagowanie odniesienia do ryciny` | 180 | 180 |
| 5 — nawias tylko-w-poprawnej | `balans opcji: nawias tylko w poprawnej` | 518 | 350 |
| 6 — zwroty kategoryczne | `złagodzenie kategorycznego dystraktora` | 201 | 94 |
| 7 — balans długości/koniunkcji/przecinka (główna tura + rozjemstwo) | różne, per pytanie (walidator, solver, rozjemca, korekty spójności wyjaśnień) | 1310 | 801 |
| 7 mini — domknięcie „najdłuższej" | `mini-przebieg: redukcja przewagi długości` | 104 | 85 |
| 8 mikro-runda 1 — token „lub" tylko-w-poprawnej | `mikroronda: wyróżnik lub` | 19 | 19 |
| przegląd końcowy — usunięcie polskiego „(obraz N)" | `mechaniczne usunięcie odniesienia do ryciny` | 86 | 86 |
| **Razem** | | **2559** | **1524** |

(Kolumna „unikalnych pytań" liczy wiersze dotknięte danym sygnałem osobno dla każdego wiersza tabeli — jedno pytanie mogło zebrać poprawki z kilku tasków, np. najpierw nawias w Tasku 5, potem balans długości w Tasku 7, więc suma tej kolumny [1756] nie jest unią. Unię po [arkusz, wiersz] dla całego planu (Taski 3–8 plus przegląd końcowy) policzono niezależnie i wynosi dokładnie 1524 — to liczba w wierszu „Razem". 11 z 19 wierszy mikro-rundy „lub" pokrywa się z wierszami dotkniętymi wcześniej przez Task 7 — stąd przyrost unii po Tasku 8 to tylko +8, nie +19. Przebieg „(obraz N)" dotknął 86 wierszy, z czego 29 pokrywało się z wierszami edytowanymi wcześniej (głównie Task 5 i Task 7 na tych samych trzech arkuszach pnia mózgu) — stąd przyrost unii to +57, nie +86.

Recount skryptem — dopasowanie po pełnej treści wpisu, nie tylko po arkusz+wiersz+ID, bo jedno pytanie zbiera wiele wpisów z różnych tasków — poprawił też dwie usterki poprzedniej wersji tej tabeli: wiersz Tasku 5 miał błędnie 519/351 zamiast 518/350, a 4 wpisy przypisane wcześniej do Tasku 6 jako „pochodne z rozjemstwa" to w rzeczywistości połączone edycje Tasku 7 — balans długości/koniunkcji, przy okazji usuwające też zwrot kategoryczny — przeniesione tu do wiersza Tasku 7; stąd 201/94 zamiast 205/98 dla Tasku 6 i 1310/801 zamiast 1305/799 dla Tasku 7.)

Liczba pytań w quizie nie zmieniła się (3355) — plan „detells" nie wykluczał ani nie dodawał pytań, wyłącznie redagował istniejącą treść.

**Uzupełnienie po przeglądzie końcowym (1 września 2026).** Przegląd tej gałęzi wykrył 86 analogicznych odniesień do ryciny źródłowej w polskiej formie „(obraz N)" — ten sam wzorzec co „Image N", ale nieuchwycony przez regex Tasku 1 (dopasowywał tylko `\bimage\b`). Odniesienia te istniały w skoroszycie od przed powstania gałęzi „detells" (transkrypcja pierwszej walidacji), skupione w trzech arkuszach pnia mózgu: `6.Rdzeń przedłużony` (29), `6.Most` (29), `6.Śródmózgowie` (28). Instrument (`measure_tells.py`) i mechaniczny stripper (`propose_image_strip.py`) rozszerzono o `\b(image|obraz)\b`/`(?:Image|obraz)` (oba warianty, bez rozróżniania wielkości liter) i usunięto wszystkie 86 tym samym mechanizmem co Task 3 (mechaniczny strip, bez LLM) — patrz wiersz „przegląd końcowy" w tabeli wyżej. Próbka 10 z 86 wynikowych zdań sprawdzona ręcznie: gramatycznie kompletne. Po tej poprawce pomiar `measure_tells.py` pokazuje **7** pozostałych trafień „image"/„obraz" (0 nawiasowych, 7 wplecionych) — nie 0. Wszystkie 7 to zweryfikowane ręcznie zwykłe użycia polskiego słowa „obraz" w znaczeniu ogólnym (np. „obraz kliniczny", „buduje obraz trójwymiarowy", „kora wzrokowa analizuje obraz"), nie odniesienia do ryciny podręcznika — rozszerzony regex, w przeciwieństwie do angielskiego „image", nieuchronnie łapie też to pospolite polskie słowo poza kontekstem cytowania ryciny. `npm run data:generate` po tej poprawce: `OK: 3355 pytań, 18 działów, 106 tematów` (bez zmiany liczby pytań). `npm test`: 12/12 bez zmian.

### Cele akceptacyjne — wynik końcowego pomiaru

Pomiar po głównym planie (Taski 1–7): `python3 scripts/validation/measure_tells.py data/neuro_questions.xlsx docs/validation/detells/final.json`

| Metryka | Baseline | Cel | Wynik (po Tasku 7) | Wynik (po mikro-rundzie „lub") | Status |
|---|---|---|---|---|---|
| odniesienia do rycin (wszystkie pola) | 321 | 0 | 0 | 0 | PASS |
| nawias tylko-w-poprawnej | 359 | ≤ 36 | 8 | 8 | PASS |
| koniunkcja tylko-w-poprawnej | 383 | ≤ 40 | 25 | 29 | PASS |
| przecinek tylko-w-poprawnej | 93 | ≤ 10 | 9 | 10 | PASS (na granicy celu) |
| kategoryczne w ≥2 błędnych | 99 | ≤ 10 | 3 | 3 | PASS |
| poprawna ≥1,5× najdłuższa | 855 | ≤ 170 (5%) | 50 | 49 | PASS |
| poprawna najdłuższa (unikatowo) | 54,5% | ≤ 35% | 35,8% | **35,5%** | **PRAWIE (0,5 pp powyżej celu)** |
| poprawna najkrótsza — strażnik regresji | 8,5% (silnie 1,5%) | ≤ 12% (silnie ≤ 3%) | 11,7% (silnie 2,5%) | 11,7% (silnie 2,5%) | PASS |

Mikro-runda „lub" (opisana w sekcji `token_ratios` niżej) lekko podniosła koniunkcję i przecinek jako efekt uboczny — część z 19 naprawionych wierszy zamieniła „lub" na „i" albo dopisała „lub" do dystraktora ze zdaniem zawierającym już przecinek. Przecinek tylko-w-poprawnej wylądował dokładnie na granicy celu (10 = ≤10), reszta zostaje bezpiecznie w normie; żaden formalny cel nie przeszedł z PASS na FAIL.

**Decyzja o pozostawieniu odstępstwa (35,5% zamiast ≤35%).** Wszystkie SILNE wyróżniki (nawias, koniunkcja, przecinek, kategoryczność, długość ≥1,5×) spadły o ≥90% względem baseline, a unia wszystkich wyróżników razem — 1182 pytania na starcie — skurczyła się do 74 (2,2%; mikro-runda „lub" dodała netto 4 pytania do unii przez efekt uboczny opisany wyżej, mimo że sama zredukowała „poprawną najdłuższą"). Resztkowy sygnał „poprawna najdłuższa" nie znika, bo część poprawnych odpowiedzi jest z natury pełną nazwą struktury anatomicznej, której nie da się skrócić bez utraty jednoznaczności (patrz przykład w dzienniku dla `PLCI-10` — rozbudowano dystraktor, bo skrócenie poprawnej odpowiedzi zepsułoby pytanie). Domykająca mini-tura Tasku 7 (91 pytań, próg selekcji: poprawna ≥1,4× drugiej najdłuższej) zredukowała ten wyróżnik z 37,0% do 35,8%; mikro-runda „lub" zdjęła go dalej do 35,5% jako efekt uboczny (5 z 19 napraw skróciły/przeformułowały poprawną opcję). Próg jednostkowego ryzyka treściowego (przebudowa dystraktora zamiast go po prostu skrócić) rośnie z każdą kolejną turą, a przewaga poprawnej nad drugą najdłuższą w pozostałych ~1190 pytaniach jest już < 1,4× (czyli poniżej progu, którym w ogóle kwalifikowano pytania do edycji w Tasku 7) — dalsze iteracje to malejące zyski przy rosnącym ryzyku zepsucia treści. Kontroler zaakceptował odstępstwo jako świadomy kompromis, nie jako przeoczenie.

### `token_ratios` — przegląd tokenów stylistycznych

Dodatkowe kryterium Tasku 8 (poza formalną tabelą wyżej) zakładało, że token „lub" zniknie z listy `token_ratios` albo spadnie poniżej ratio 2. Pierwszy pomiar po Tasku 7 pokazał, że tak się nie stało (ratio 25,0 — 25 wystąpień w poprawnych opcjach vs 3 w błędnych) i że żaden task planu nie mierzył ani nie korygował tego tokenu wprost (detektor koniunkcji z Tasku 1 łapie tylko „i"/„oraz", nie „lub") — luka opisana tu jako „pozostawiona" trafiła od razu do osobnej mikro-rundy poprawek (ten sam mechanizm co Task 5/6: edytor + kontroler na dossier, bez rozjemcy — ryzyko było niskie).

**Wynik mikro-rundy 1.** Selekcja (`scripts/validation/prepare_lubpass.py`, wyróżnik „lub_only" — dokładnie ten sam wzorzec co `only_correct()` dla pozostałych telli) dała 25 kandydatów: pytania, w których „lub" występuje wyłącznie w poprawnej opcji. Edytor zaproponował 25 poprawek w dwóch stylach: dopisanie „lub X" do dystraktora (14 przypadków — rozcieńcza sygnał bez ruszania poprawnej odpowiedzi) albo zamianę „lub" na „i"/przeformułowanie samej poprawnej opcji (11 przypadków, w tym 5 przyjętych). Kontroler zweryfikował każdą zmianę względem dossier: 19 CZYSTO, 6 ZASTRZEŻENIE. Wszystkie 6 zastrzeżeń dotyczyły tego samego ryzyka: zamiana „lub" (alternatywa — którykolwiek z czynników) na „i" (koniunkcja — oba naraz) w poprawnej opcji, gdzie albo dossier nie zawierał fragmentu pozwalającego to zweryfikować, albo (w jednym przypadku, `15.Znaczenie kliniczne` w.11) wprost zaprzeczał: źródło opisuje to zwężenie drobnych naczyń tętniczych jako reakcję na silne emocje albo na zimno — dwa niezależne, rozłączne wyzwalacze tego samego zjawiska, nie stan wymagający ich jednoczesnego wystąpienia (str. 147), więc zamiana na koniunkcję zmieniłaby sens. Te 6 wierszy zostawiono w stanie sprzed poprawki (`docs/validation/detells/dropped-lub.json`) — status quo, nie regresja. 19 zweryfikowanych poprawek naniesiono (`docs/validation/detells/props-lub-ok.json` → applier, 0 odrzuceń).

**Rezultat**: token „lub" — correct 25→20, wrong 3→17, ratio **25,0 → 3,5** (nadal na liście `token_ratios`, próg `cc≥20` nie został przekroczony w dół — surowe liczby potwierdzone niezależnym skryptem regex poza `measure_tells.py`). Wyróżnik „lub_only" (tylko poprawna zawiera „lub") spadł z 25 do dokładnie 6 — czyli do liczby wierszy pozostawionych przez kontrolera ze względów treściowych, nie z braku starań. Domknięcie pozostałych 6 wymagałoby innej strategii niż „lub→i" (np. rozbudowa dystraktora zamiast przeformułowania poprawnej), co zostawiono na ewentualną kolejną rundę.

Pozostałe pozycje listy po mikro-rundzie (niezmienione względem pomiaru sprzed niej): „bocznym" (3,6), „lub" (3,5, opisane wyżej), „hipokampa" (3,5), „bruzdy" (3,2), „między" (2,9), „tak" (2,5), „części" (2,2), „tylnej" (2,1), „blaszki" (2,0) — próbka 3 przykładów na token potwierdza charakter merytoryczny/anatomiczny (terminy topograficzne skupione tematycznie: boczność, hipokamp, bruzdy, relacje przestrzenne „między X a Y"), nie stylistyczny. Wyjątek: „tak" (2,5, 49 wystąpień w poprawnych vs 60 w błędnych) pochodzi z pytań tak/nie („Czy X posiada Y?") — to nie jest tell długości czy stylu, tylko nierówny rozkład odpowiedzi twierdzących/przeczących w tej podgrupie pytań; poza zakresem tego planu (żaden task go nie adresował), ale wart odnotowania jako osobna kategoria ryzyka na przyszłość.

### Testy i sanity-check aplikacji

`npm run data:generate` → `OK: 3355 pytań, 18 działów, 106 tematów` (bez ostrzeżeń o cytowaniu liter, bez błędów). `python3 -m pytest scripts/ -v` → 13 passed. `npm test` (vitest) → 12 passed, zgodnie z baseline sprzed planu. `npm run dev` na porcie 8080 odpowiedział HTTP 200; `public/data/sections/9.json` i `10.json` po regeneracji nie zawierają już żadnego dopasowania „image" (wcześniej to właśnie te dwa działy niosły odniesienia do rycin); próbka 5 losowych pytań z różnych działów ma po 4 opcje, niepuste i parami różne. Regeneracja powtórzona po mikro-rundzie „lub" (`npm run data:generate` → `OK: 3355 pytań`, `npm test` → 12 passed) — `public/data/` odzwierciedla teraz wszystkie 19 poprawek tej rundy (11 dotkniętych działów w diffie).

### Czego nauczyła ta sesja

**Wąski regex zostawia sąsiednie wzorce nietknięte.** Detektor koniunkcji mierzył tylko „i"/„oraz" — token „lub" niósł silniejszy sygnał (ratio 64→25) i nigdy nie trafił do żadnej tury korekt, bo żaden task go nie szukał. Miernik akceptacyjny trzeba traktować jako listę TYLKO zmierzonych zjawisk, nie dowód kompletności.

**Twardy próg selekcji ogranicza też wielkość poprawki.** Mini-tura Tasku 7 wzięła tylko pytania z przewagą długości ≥1,4× — świadomie zostawiła resztkę tuż poniżej progu, bo dalsze schodzenie z progiem oznaczało edycję pytań, gdzie poprawna odpowiedź jest z natury pełną nazwą i skrócenie zepsułoby jednoznaczność.

**Baseline i pomiar końcowy muszą liczyć identycznie.** Cała tabela akceptacyjna działa tylko dlatego, że `measure_tells.py` się nie zmienił między Taskiem 1 a Taskiem 8 — każda zmiana definicji w trakcie planu unieważniłaby porównanie.

**Zamiana alternatywy na koniunkcję to osobna kategoria ryzyka, nie kosmetyka.** Wszystkie 6 zastrzeżeń kontrolera w mikro-rundzie „lub" miały jedną wspólną przyczynę: „X lub Y" (którykolwiek z czynników) przeformułowane na „X i Y" (oba naraz) subtelnie zmienia twierdzenie, a dossier rzadko ma fragment wystarczająco dosłowny, by to zweryfikować w jedną albo drugą stronę. Bezpieczniejsza domyślna strategia (14 z 19 przyjętych poprawek) to dopisanie „lub" do dystraktora, nie ruszanie poprawnej opcji wcale.
