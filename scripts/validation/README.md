# Potok walidacji pytań

Narzędzia do sprawdzania pytań z `data/neuro_questions.xlsx` względem podręcznika
„Neuroanatomia. Ekspresowo." C.P. Krasuckiego. Wszystkie działają lokalnie, bez modeli.

## Warunek wstępny: transkrypcja źródła

`docs/source-text/` zawiera dosłowną transkrypcję skanu (strony PDF 8–172, bez luk).
Katalog jest w `.gitignore` — to materiał chroniony prawem autorskim, prywatny indeks
do weryfikacji. **Przelicznik: strona PDF = strona książki − 3.**

Jeśli katalog nie istnieje, trzeba go odtworzyć: przepisać skan paczkami po 5–6 stron,
z nagłówkiem `## [PDF <n> | str. książki <m>]` przed każdą stroną. Paczki po 15 stron
bywają odrzucane ze względu na objętość reprodukcji.

## Kolejność uruchamiania

```bash
python3 scripts/validation/export_topics.py     # xlsx -> JSON per temat (do scratchpada)
python3 scripts/validation/build_dossiers.py    # dossier źródłowe per jednostka walidacyjna
```

`export_topics.py` rozbija 106 arkuszy na osobne pliki JSON.
`build_dossiers.py` składa dla każdej jednostki wycinek podręcznika: strony wskazane
ręcznie w `anchors.py` (mapa temat → strony, wyprowadzona ze spisu treści) plus kilka
dobranych automatycznie przez cosine tf-idf jako materiał pokrewny.

**Jednostka walidacyjna ≠ arkusz.** Dwa arkusze łączą po kilka podtematów pod jedną
nazwą: `6.Śródmózgowie` (150 pytań, bloki POKR/KOMO/ISCZ/JACZ/WOMO) i `8.Hipokamp`
(120 pytań, HIBU/HIPO/HIFU/HIKL). Bloki rozpoznaje się po prefiksie kolumny ID.
Dlatego jednostek jest 114, nie 106.

## Narzędzia jednorazowe

- `dedupe.py` — oznacza jako wykluczone kopie pytań powtórzonych w kilku tematach
  (tabela decyzji z uzasadnieniem wewnątrz pliku)
- `find_cjk.py` — szuka znaków spoza alfabetu łacińskiego wklejonych do treści

## Kolumna „Wykluczone"

Kolumna J w każdym arkuszu pytań. Wartość `TAK` oznacza pytanie wadliwe merytorycznie
albo duplikat; `generate_quiz_data.py` je pomija (`is_excluded()`). Wiersz zostaje
w arkuszu, więc decyzja jest odwracalna.

## Ślad audytowy

`docs/validation/` — raporty (`REPORT.md`, `REVIEW-82.md`, `ADJUDICATION.md`),
surowe znaleziska per jednostka oraz `applied-changes.json`: każda zmiana wpisana
do xlsx z wartością sprzed, uzasadnieniem i źródłem sygnału.

## Zasady, które wyszły z pierwszego, nieudanego podejścia

1. **Nie każ agentom masowo czytać stron skanu.** Strona to obraz, zostaje w kontekście
   i jest przesyłana ponownie w każdej turze. Pierwsze podejście spaliło 63 mln tokenów
   na jednej trzeciej zbioru. Praca na transkrypcji kosztuje ~2,4 tys. tokenów na pytanie,
   praca na skanie ~11,6 tys.
2. **Skan tylko do rozstrzygania sporów**, i grupowany po stronach — jeden agent czyta
   zakres stron raz dla wielu pytań, zamiast każdy dla swojego.
3. **Agent zapisuje wynik na dysk, zanim go zwróci.** Przy trafieniu w limit wyniki
   z pamięci przepadają, pliki zostają.
4. **Dwa niezależne sygnały przed zmianą klucza.** Walidator widzący klucz i solver
   rozwiązujący na ślepo mylą się w różnych miejscach — z 82 spornych przypadków połowa
   okazała się fałszywym alarmem.
5. **Sprawdź przesunięcie wierszy.** Agent potrafi odpowiedzieć poprawnie, ale przypisać
   odpowiedzi do sąsiednich wierszy. Test: policz zgodność przy przesunięciu o ±1 —
   skok o kilkadziesiąt punktów procentowych zdradza defekt.
