# -*- coding: utf-8 -*-
"""Buduje dossier źródłowe per jednostkę walidacyjną.

Dossier = strony podręcznika przypisane do tematu przez ręczną mapę ANCHORS (ze spisu treści),
uzupełnione o kilka stron dobranych automatycznie (cosine tf-idf) jako materiał pokrewny.
Bez tokenów LLM.
"""
import json, glob, os, re, sys, math, unicodedata, collections

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HERE = os.path.dirname(os.path.abspath(__file__))
# Katalog roboczy poza repo — patrz export_topics.py. Kotwice (anchors.py) leżą obok skryptu.
SCR = os.environ.get('NEURO_WORK_DIR') or os.path.join(REPO, '.validation-work')
TRANS = os.path.join(REPO, 'docs', 'source-text')
OUT = os.path.join(SCR, 'dossiers')
sys.path.insert(0, HERE)

STOP = set('''i oraz w z na do od po przez dla lub albo jest sa to co ktora ktory ktore ktorego ktorej jaka jaki jakie
sie nie tak tez przy nad pod przed za miedzy o a ale czy jako ze gdzie ile jego jej ich tym ten ta te
czesc czesci budowa opis rodzaj rodzaje glowny glowna glowne wystepuje wystepuja znajduje znajduja stanowi
struktura struktury element elementy'''.split())


def norm(s):
    s = str(s if s is not None else '').lower().replace('ł', 'l')
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r'[^a-z0-9 ]+', ' ', s)


def stem(w):
    """Prymitywny stemmer dla polskiego — obcina typowe końcówki fleksyjne."""
    for suf in ('ego', 'emu', 'ych', 'ymi', 'ami', 'owi', 'ach', 'iem', 'em', 'ie', 'ia',
                'y', 'i', 'a', 'e', 'u', 'o', 'ow'):
        if len(w) > 5 and w.endswith(suf):
            return w[:-len(suf)]
    return w


def toks(s):
    return [stem(w) for w in norm(s).split() if len(w) > 3 and w not in STOP]


def load_pages():
    """Zwraca listę stron [{'pdf','book','text','src'}] ze wszystkich transkrypcji."""
    pages = {}
    for fp in sorted(glob.glob(os.path.join(TRANS, 'pdf-*.md'))):
        t = open(fp).read()
        parts = re.split(r'^## \[PDF (\d+)\s*\|\s*str\. książki ([^\]]*)\]', t, flags=re.M)
        for i in range(1, len(parts), 3):
            pdf = int(parts[i])
            pages[pdf] = {'pdf': pdf, 'book': parts[i + 1].strip(), 'text': parts[i + 2].strip(),
                          'src': os.path.basename(fp)}
    return [pages[k] for k in sorted(pages)]


def build_units():
    """Jednostka = arkusz albo blok podtematu (prefiks ID) w arkuszu ponadwymiarowym."""
    units = []
    for fp in sorted(glob.glob(os.path.join(SCR, 'topics', '*.json'))):
        d = json.load(open(fp))
        blocks = collections.OrderedDict()
        for q in d['questions']:
            m = re.match(r'^([A-Za-z]+)-\d+$', str(q['id'] or ''))
            blocks.setdefault(m.group(1) if m else 'X', []).append(q)
        multi = len(blocks) > 1
        for pref, qq in blocks.items():
            units.append({
                'unitId': f"{d['sheet']}|{pref}" if multi else d['sheet'],
                'sheet': d['sheet'], 'file': os.path.basename(fp), 'idPrefix': pref,
                'sectionId': d['sectionId'], 'sectionTitle': d['sectionTitle'], 'topicTitle': d['topicTitle'],
                'rowFrom': qq[0]['row'], 'rowTo': qq[-1]['row'], 'count': len(qq), 'questions': qq,
            })
    return units


def anchor_pages(unit_id, pages):
    """Indeksy stron wskazanych ręcznie w mapie ANCHORS."""
    from anchors import ANCHORS
    key = unit_id if unit_id in ANCHORS else unit_id.split('|')[0]
    ranges = ANCHORS.get(key)
    if not ranges:
        return [], False
    idx = []
    for i, p in enumerate(pages):
        digits = re.sub(r'\D', '', p['book'])
        if not digits:
            continue
        b = int(digits)
        if any(a <= b <= z for a, z in ranges):
            idx.append(i)
    return idx, True


def main(top_pages=6):
    pages = load_pages()
    print(f'stron źródła: {len(pages)}')
    df = collections.Counter()
    page_tf = []
    for p in pages:
        tf = collections.Counter(toks(p['text']))
        page_tf.append(tf)
        df.update(tf.keys())
    N = len(pages)
    idf = {w: math.log(N / (1 + c)) for w, c in df.items()}

    units = build_units()
    os.makedirs(OUT, exist_ok=True)
    manifest, missing_anchor = [], []
    for u in units:
        qtext = ' '.join(' '.join(str(q.get(k) or '') for k in ('question', 'A', 'B', 'C', 'D'))
                         for q in u['questions'])
        qtf = collections.Counter()
        for _ in range(10):                       # tytuł tematu waży 10x
            qtf.update(toks(u['topicTitle'] + ' ' + u['sectionTitle']))
        qtf.update(toks(qtext))
        qvec = {w: (1 + math.log(c)) * idf.get(w, 0) for w, c in qtf.items() if w in idf}
        qnorm = math.sqrt(sum(v * v for v in qvec.values())) or 1
        scores = []
        for i, tf in enumerate(page_tf):
            pvec = {w: (1 + math.log(c)) * idf.get(w, 0) for w, c in tf.items()}
            pnorm = math.sqrt(sum(v * v for v in pvec.values())) or 1
            scores.append((sum(v * pvec[w] for w, v in qvec.items() if w in pvec) / (qnorm * pnorm), i))
        scores.sort(reverse=True)

        anchors, has_anchor = anchor_pages(u['unitId'], pages)
        if not has_anchor:
            missing_anchor.append(u['unitId'])
        extra = [i for _, i in scores if i not in set(anchors)][:top_pages]
        chosen = sorted(set(anchors) | set(extra))

        body = [f"# Dossier źródłowe — {u['sectionTitle']} / {u['topicTitle']}"
                f"{(' [blok ' + u['idPrefix'] + ']') if '|' in u['unitId'] else ''}",
                f"Strony {', '.join(pages[i]['book'] for i in anchors)} to rozdział podręcznika przypisany "
                f"do tego tematu; pozostałe dołączono jako materiał pokrewny.",
                "Numer strony KSIĄŻKI podawaj w cytatach. Jeśli odpowiedzi nie ma w tym materiale — "
                "to nie jest błąd merytoryczny.", ""]
        for i in chosen:
            p = pages[i]
            body.append(f"## [str. książki {p['book']} | PDF {p['pdf']}]")
            body.append(p['text'])
            body.append("")
        slug = re.sub(r'[^a-z0-9]+', '-', norm(u['unitId'])).strip('-')
        open(os.path.join(OUT, f'{slug}.md'), 'w').write('\n'.join(body))
        manifest.append({'unitId': u['unitId'], 'sheet': u['sheet'], 'file': u['file'], 'idPrefix': u['idPrefix'],
                         'sectionId': u['sectionId'], 'sectionTitle': u['sectionTitle'],
                         'topicTitle': u['topicTitle'], 'rowFrom': u['rowFrom'], 'rowTo': u['rowTo'],
                         'count': u['count'], 'dossier': f'dossiers/{slug}.md',
                         'dossierChars': sum(len(pages[i]['text']) for i in chosen),
                         'anchorPages': [pages[i]['book'] for i in anchors],
                         'bookPages': [pages[i]['book'] for i in chosen]})

    # sprzątanie osieroconych plików z wcześniejszych przebiegów
    keep = {os.path.basename(m['dossier']) for m in manifest}
    for f in glob.glob(os.path.join(OUT, '*.md')):
        if os.path.basename(f) not in keep:
            os.remove(f)

    json.dump(manifest, open(os.path.join(SCR, 'units-manifest.json'), 'w'), ensure_ascii=False, indent=1)
    avg = sum(m['dossierChars'] for m in manifest) / len(manifest)
    print(f"jednostek: {len(manifest)} | pytań: {sum(m['count'] for m in manifest)} | "
          f"średnie dossier: {avg/1024:.1f} KB (~{avg/3.5:.0f} tokenów)")
    print(f'jednostek BEZ kotwicy: {len(missing_anchor)} {missing_anchor}')
    for t in ['9.Istota czarna', '13.VII', '12.Wodociąg mózgu', '18.Układ wzrokowy']:
        m = next(x for x in manifest if x['unitId'].startswith(t))
        extra = [p for p in m['bookPages'] if p not in m['anchorPages']]
        print(f"  {m['unitId']:26} kotwica: {','.join(m['anchorPages'])}  + {','.join(extra)}")


if __name__ == '__main__':
    main()
