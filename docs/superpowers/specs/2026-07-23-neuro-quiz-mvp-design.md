# Neuro Świry — projekt MVP publicznego quizu

Data: 2026-07-23
Status: zatwierdzone; kolejność realizacji ustalona

## Kolejność realizacji

1. **Plan 1 — potok danych** (`plans/2026-07-23-neuro-quiz-data-pipeline.md`):
   generator Python → `public/data/*.json` + schematy `zod`.
2. **Przepisanie wyjaśnień** (operacja jednorazowa, spec sekcja 6): model + QC na
   `data/neuro_questions.xlsx`. Prerekwizyt losowania odpowiedzi.
3. **Plan 2 — aplikacja** (do napisania po Planie 1): konsumpcja manifestu,
   wielokrotny wybór działów, podłączenie quizu, **losowanie odpowiedzi od razu**,
   zdjęcie zaszytej taksonomii i 18 tras, config deployu Netlify.

## 1. Cel i odbiorca

Publiczna strona z quizem z neuroanatomii dla grupy studentów jednego roku.
Użycie: regularne, w ciągu całego semestru. Zero kont, zero logowania, zero
przychodu — narzędzie do nauki dla zamkniętej grupy, dostępne publicznie pod
własną domeną.

Dodatkowy wymóg: dodawanie i zmiana pytań przez uruchomienie skryptu ze wskazaniem
pliku xlsx. Strona ma być generyczna — nic o liczbie działów, tematów ani ich
nazwach nie jest zaszyte w kodzie.

## 2. Dane

Źródło prawdy: `neuro_questions.xlsx` (edytowany ręcznie przez autora).

Stan zweryfikowany (pomiar na `questions.csv`, 2026-07-23):
- 3389 pytań, 18 działów, 106 tematów (par dział–temat).
- Najmniejszy dział: 119 pytań („Ogólne"). Największy: 360 („Nerwy czaszkowe").
  Pozostałe 120–240.
- Każde pytanie: treść, 4 warianty A–D, jedna poprawna, wyjaśnienie, tagi.
- 926 unikalnych tagów, z czego 452 użyte tylko raz (mediana 2 użycia).
- Rozkład poprawnych odpowiedzi jest skośny: B=1277 (37,7%), C=851, A=818,
  D=443 (13,1%).
- Cały zbiór jako jeden JSON: ~359 KB po gzipie.
- Dane są w całości tylko do odczytu dla użytkownika końcowego.

Liczby (18, 106) są tu wyłącznie stanem faktycznym danych na dziś — NIE są
założeniem projektu. Aplikacja i skrypt wyprowadzają je z zawartości xlsx.

## 3. Architektura: bez bazy, generyczna aplikacja nad manifestem

Brak serwera bazy, sekretów, keep-alive. Dane read-only o rozmiarze ~359 KB gzip —
baza w tej skali to koszt operacyjny bez korzyści. Wariant porównany wcześniej
z Supabase (pauzowanie projektu po 7 dniach bezczynności, brak backupów na Free)
i Cloudflare D1 (przepisanie schematu z Postgresa na SQLite, wymóg backendu) —
oba przegrywają dla tego przypadku.

Zasada naczelna: **aplikacja jest generycznym czytnikiem manifestu.** Offline'owe
narzędzie admina generuje z xlsx manifest (spis działów i tematów) oraz pliki pytań;
aplikacja renderuje interfejs z tego, co znajdzie w manifeście. Ile działów wyszło
z danych, tyle pojawia się na ekranie. W kodzie nie ma listy kategorii ani liczby „18".

Podział ról:
- **Generator to narzędzie admina, nie część builda strony.** Skrypt w Pythonie
  (rozszerzenie istniejącego `xlsx_to_csv.py`), uruchamiany lokalnie przez autora.
  Nikt nie wskazuje pliku „z poziomu strony" — admin odpala skrypt u siebie.
- **Aplikacja (JS) tylko czyta wygenerowane JSON-y.** Nie generuje niczego, nie
  dotyka xlsx.

Konsekwencja: cała obsługa treści to `python3 generate.py <ścieżka.xlsx>` → commit
→ push → deploy. Nowy dział/temat/pytanie w xlsx pojawia się na stronie bez żadnej
zmiany w kodzie. Backup jest darmowy i wynika z gita (xlsx + skrypt + wygenerowane
JSON-y w repo).

Ponieważ generator jest w Pythonie, a aplikacja w TypeScript, nie ma współdzielonych
typów pilnujących zgodności formatu. Odzyskujemy to inaczej: **aplikacja waliduje
wczytany JSON schematem `zod`** (jest w zależnościach projektu). Rozjazd formatu
generatora z oczekiwaniami strony wywala się głośno przy wczytaniu, zamiast po cichu
pokazać śmieci.

## 4. Potok danych — dwie operacje na skryptach

### 4a. Jednorazowo: przepisanie wyjaśnień w xlsx

Osobny, świadomy krok uruchamiany raz (szczegóły w sekcji 6). Modyfikuje samo
`neuro_questions.xlsx`. NIE jest częścią generowania plików strony — nie chcemy
przy każdym imporcie na nowo przepisywać już czystych wyjaśnień.

### 4b. Przy każdej zmianie treści: generowanie plików strony

Skrypt w Pythonie (**rozszerzenie istniejącego `xlsx_to_csv.py`**), biorący
**ścieżkę do xlsx jako argument**. Istniejący skrypt już czyta xlsx, odwraca
autokonwersje Excela (`cell_text`), parsuje tagi (`parse_tags`), waliduje i odrzuca
złe wiersze oraz mapuje Strukturę na arkusze — zmienia się tylko etap zapisu:
zamiast jednego CSV wypluwa JSON-y strony do `public/data/`. Generuje:

1. **`public/data/index.json` (manifest)** — spis działów, każdy z id, tytułem,
   listą tematów, licznikami pytań i wskaźnikiem do swojego pliku z pytaniami.
   id brane z danych.
2. **`public/data/sections/<id>.json`** — pliki pytań per dział, ładowane leniwie
   przez aplikację dopiero gdy dział wchodzi do testu.

`public/` jest katalogiem statyków serwowanym przez Netlify — to jest „katalog
resources", o którym mowa w obiegu publikacji (sekcja 8).

**Walidacja żyje w tym skrypcie i jest pierwszą bramką jakości.** Skrypt jest
głośnym gate'em — złe dane zatrzymują generowanie, więc nigdy nie trafią na stronę.
Istniejący `xlsx_to_csv.py` już to robi (odrzuca puste warianty, złą „Poprawną",
powtórzone nagłówki); dochodzą:
- `correct_answer` należy do zbioru {A,B,C,D} — mapowane na indeks 0–3 z walidacją
  zbiorem (obecny skrypt już to sprawdza przy odrzucaniu);
- **wyjaśnienia nie cytują liter** — jeśli po jednorazowym przepisaniu (4a) trafi
  się nowe pytanie z wyjaśnieniem odwołującym się do litery, skrypt OSTRZEGA
  (nie blokuje — żeby plan był wykonalny przed przepisaniem), więc dopisane później
  treści nie prześlizgną się niezauważone.

Druga bramka jest po stronie aplikacji: **`zod` waliduje wczytany JSON** (sekcja 3),
łapiąc rozjazd formatu, którego Python nie wychwyci brakiem współdzielonych typów.

Klucz tematu to zawsze para (dział, temat) — 6 nazw tematów powtarza się między
działami (np. „Znaczenie kliniczne" w 5 działach), więc sam slug tematu jest
niejednoznaczny.

Format wszystkich plików strony: **JSON** — natywny dla przeglądarki, bez parsera
i jego pułapek. `xlsx_to_csv.py` może dalej wypluwać CSV jako produkt uboczny
(np. do ewentualnej bazy), ale strona konsumuje JSON.

## 5. Przepływ użytkownika

1. **Ekran startowy** — aplikacja ładuje `index.json` i renderuje listę działów
   do zaznaczania (wiele naraz) z opcją „zaznacz wszystkie". Osobno selektor liczby
   pytań: 10 / 20 / 30 / 50 / wszystkie. Wszystko wyprowadzone z manifestu.
2. **Start testu** — z zaznaczonych działów aplikacja dogrywa ich pliki pytań
   (ścieżki z manifestu) i buduje wspólną pulę. Wybrana liczba to **liczba łączna
   z całej puli** (nie per dział). „Wszystkie" = wszystkie pytania z sumy zaznaczonych
   działów. Pula jest przemieszana (pytania z różnych działów przeplatają się).
3. **Quiz** — pytanie po pytaniu, warianty A–D w **losowej kolejności**,
   natychmiastowe wyjaśnienie po odpowiedzi, pasek postępu. Obsługa klawiatury
   A/B/C/D + Enter (już istnieje).
4. **Wynik** — liczba poprawnych/błędnych, procent. Opcja „popraw błędne" zawęża
   zestaw do błędnie odpowiedzianych i uruchamia je ponownie (już istnieje).
5. **Koniec sesji** — nic nie jest zapamiętywane. Odświeżenie/zamknięcie karty
   kasuje stan. Brak localStorage, brak kont.

Liczby zawsze się mieszczą: minimum jednego działu to 119 pytań, więc każda opcja
selektora (do 50) działa nawet przy jednym zaznaczonym dziale.

## 6. Losowanie odpowiedzi i przepisanie wyjaśnień (operacja jednorazowa)

Kolejność odpowiedzi jest losowana, by zlikwidować wyuczalną przewagę odpowiedzi B
(37,7% poprawnych w stałej kolejności).

Blokada: wyjaśnienia odwołują się do liter pozycyjnie („Odpowiedź B jest poprawna",
„A i C to układ obwodowy"). Po przetasowaniu litery kłamią. Pomiar (2026-07-23):
- 936 wyjaśnień (27,6%) cytuje literę wprost;
- do 2377 (70,1%) ma luźniejsze odwołania literowe.

Decyzja: **jednorazowo przepisujemy wszystkie wyjaśnienia tak, by cytowały treść
odpowiedzi zamiast liter**, a wynik wraca do `neuro_questions.xlsx` (plik zostaje
źródłem prawdy — inaczej każdy kolejny eksport przywracałby litery).

Wykonanie: transformacja modelem z kontrolą jakości na próbce, backup xlsx przed
operacją. To ~3389 tekstów w swobodnej polszczyźnie — część wymaga ręcznej korekty,
więc zakłada się przegląd wyników. Po tej operacji egzekwuje ją już walidacja
w skrypcie generującym (sekcja 4b) — nowe pytania z literami są odrzucane.

Przykład:
- przed: „OUN tworzy mózgowie i rdzeń. A i C to układ obwodowy. D to struktury
  zaopatrywane."
- po: „OUN tworzy mózgowie i rdzeń. Nerwy czaszkowe oraz zwoje czuciowe to układ
  obwodowy. Mięśnie gładkie i skóra to struktury zaopatrywane."

## 7. Zmiany w istniejącym kodzie

Aplikacja (TanStack Start, React 19, TanStack Router, Tailwind 4, shadcn/ui) ma
gotowy UI quizu, ale nie jest podłączona do danych i ma zaszytą taksonomię. Do
zrobienia:

- **Zdjąć zaszytą taksonomię** — dziś `src/lib/categories.ts` to ręcznie wpisane
  18 kategorii i 102 podkategorie, rozjechane z danymi (patrz niżej). Zastąpić
  runtime'owym wczytaniem `index.json`. Nazwy i liczba działów pochodzą z manifestu,
  nie z modułu w kodzie.
- **Schemat i walidacja danych (`zod`)** — zdefiniować w aplikacji schematy `zod`
  dla manifestu i pytania (typy TS wyprowadzone przez `z.infer`). Wczytany JSON
  jest walidowany przy ładowaniu — to druga bramka jakości, łapiąca rozjazd formatu
  generatora (Python) z oczekiwaniami strony.
- **Model pytania** — typ `Question` wyprowadzony ze schematu `zod`: `section`,
  `topic`, `question`, `options` (4), `correctIndex` (0–3, zwalidowany przez skrypt),
  `explanation`, `tags`. Zastępuje dzisiejszy płaski `QuizQuestion` (tylko `category`).
- **Przekazanie zakresu** — `TestSettings` (`navigate({ to: "/quiz" })` bez
  parametrów) musi przekazać zaznaczone działy i liczbę; `quiz.tsx` potrzebuje
  `validateSearch` + loadera zamiast stałego `MOCK_QUESTIONS`.
- **Wielokrotny wybór działów** — ekran startowy dziś oferuje albo jeden dział,
  albo „wszystkie"; dodać zaznaczanie wielu, renderowane z manifestu.
- **Selektor liczby** — dziś martwy (wartość w stanie, nigdzie nieprzekazywana);
  podłączyć.
- **Tagi** — usunąć z UI atrapę 10 hardkodowanych tagów (3 nie istnieją w danych);
  tagi zostają w danych, ale nie w interfejsie.
- **Trasy** — 18 statycznych plików `src/routes/<slug>.tsx` (identyczny boilerplate)
  zastąpić jednym ekranem startowym z wielokrotnym wyborem + jedną trasą quizu.
  Ewentualna trasa pojedynczego działu renderowana generycznie z manifestu. Nowy
  dział nie wymaga wtedy nowego pliku trasy.
- **Usunąć `mock-questions.ts`** po podłączeniu realnych danych.

Rozjazd naprawiony przez zdjęcie zaszytej taksonomii: dziś kod gubi 180 pytań
(5,3%) — dział „Kresomózgowie" ma w kodzie 4 tematy zamiast 8 (brak 5 tematów
„Kora mózgu - płat …" i „Wyspa" = 150 pytań, plus nadmiarowe „Kora mózgu",
którego w danych nie ma) oraz literówka „Czucie powierzchowne" vs „Czucie
powierzchniowe" (30 pytań). Generowanie z jednego źródła usuwa tę klasę błędów.

Drobne naprawy przy okazji:
- `$category.$subcategory.tsx:55` linkuje do `to="/$category"` — trasa nieobecna
  w `routeTree.gen.ts` (0 trafień), ryzyko przy prerenderze.
- `sitemap[.]xml.ts:4` — zahardkodowany `BASE_URL`; po zmianie domeny sitemap kłamie;
  pokrywa tylko 18 kategorii + `/`, pomija tematy i `/quiz`. Powinien też wynikać
  z manifestu.
- `ogolne.tsx:8` — literówka w tytule SEO: „Ogólnew — Neuro Świry".

## 8. Hosting: Netlify Free

Wybór: **Netlify Free** z własną domeną (potwierdzone cytatami z dokumentacji
dostawcy, 2026-07-23).

- Własna domena + darmowy auto-odnawiany SSL — w planie Free.
- Brak klauzuli niekomercyjnej (Vercel Hobby zabrania komercji — istotne, gdyby
  projekt kiedyś ewoluował).
- Auto-deploy z GitHuba po pushu.
- Preview/branch deploye nielimitowane i darmowe (0 kredytów); production deploy = 15
  kredytów z budżetu 300/mies. → ~20 wdrożeń produkcyjnych/mies. Przy rzadkich
  aktualizacjach to sufit nieosiągalny.

**Obieg dwóch gałęzi (develop → main):**

- `develop` — gałąź robocza. Push tam wyzwala **branch deploy** (0 kredytów) pod
  własnym URL `develop--<site>.netlify.app`. To żywa, klikalna wersja strony
  z nowymi danymi — podglądasz ją PRZED publikacją.
- `main` — gałąź produkcyjna, ma własną domenę + SSL. Merge `develop → main` wyzwala
  **production deploy** (15 kredytów) i publikuje na żywej domenie.
- Branch deploye włącza się raz: *Site configuration → Build & deploy → Branches
  and deploy contexts → Configure* → dodać `develop` (albo „All").
  (Zweryfikowane: docs.netlify.com/deploy/deploy-types/branch-deploys/,
  .../deploy-previews/.)

Pełny obieg aktualizacji pytań:
```
1. python3 generate.py neuro_questions.xlsx     → JSON do public/data/
2. git add public/data/ && git commit && git push origin develop
3. Netlify: branch deploy (0 kredytów) → sprawdź develop--<site>.netlify.app
4. OK → merge develop → main
5. Netlify: production deploy (15 kredytów) → żywa strona na domenie
```

Uwaga o Lovable: push na *podpiętą* gałąź synchronizuje się do edytora Lovable
(`AGENTS.md`). Do której gałęzi Lovable jest podpięty — potwierdzić przy konfiguracji;
docelowo praca na `develop` nie zaśmieca edytora, a merge do `main` synchronizuje
i publikuje jednocześnie.

Koszt setupu (jednorazowo, wchodzi do planu wdrożenia): plugin
`@netlify/vite-plugin-tanstack-start`, wpis w `vite.config.ts`, plik `netlify.toml`,
włączenie branch deployów dla `develop`.

Ograniczenie do świadomego utrzymania: wspólny budżet 300 kredytów dotyczy
wszystkich projektów na koncie — przekroczenie pauzuje wszystkie strony. Przy tej
skali (kilkadziesiąt osób, ~360 KB) nierealne.

Uwaga o Lovable: repo `adamdrzewiecki/neuro-wiry-hub` jest podpięte do Lovable.
`AGENTS.md` zakazuje force-push/rebase/amend/squash na wypchniętych commitach —
skrypt importu musi robić zwykłe commity na `main`. Lovable pozostaje możliwym
edytorem; hostingiem produkcyjnym jest Netlify.

## 9. Poza zakresem MVP (świadomie odłożone)

- Konta użytkowników i synchronizacja postępu między urządzeniami (wymagałoby
  backendu — wtedy Supabase, z jego pauzowaniem).
- Pamięć w przeglądarce (historia błędów, wznowienie testu, statystyki opanowania).
- Filtrowanie po tagach w UI (tagi zostają w danych na przyszłość).
- Ocenianie/ranking/certyfikaty (wymagałoby ukrycia odpowiedzi po stronie serwera).

## 10. Rzeczy niezweryfikowane (do sprawdzenia w fazie wdrożenia)

- Czy aplikacja wymaga SSR, czy po przejściu na generyczne wczytywanie manifestu
  da się ją zbudować jako statyczne SPA (mniej ruchomych części na Netlify) —
  do rozstrzygnięcia w planie.
- Czy `@lovable.dev/vite-tanstack-config` w repo jest w wersji wspierającej
  wybrany preset — do sprawdzenia w `package.json`.
- Próg leniwego ładowania i ewentualny osobny plik wyjaśnień (najdłuższe pole) —
  do ustalenia pomiarem po podłączeniu danych; przy 359 KB gzip całości może się
  okazać zbędny.
