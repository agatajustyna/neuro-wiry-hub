# -*- coding: utf-8 -*-
"""Buduje dossier dla POJEDYNCZYCH pytań, nie dla całych tematów.

Dossier tematyczne ma ~29 KB i przy kilkudziesięciu jednostkach to ono, a nie liczba
pytań, decyduje o koszcie. Tutaj dla każdego pytania wyszukujemy najtrafniejsze strony
(cosine tf-idf po treści pytania i opcji), a potem grupujemy pytania tak, aby agent
dostał sumę stron swojej grupy — zwykle kilkukrotnie mniej tekstu.

Użycie: importowany przez skrypty przygotowujące paczki walidacyjne.
"""
import collections
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_dossiers import load_pages, toks  # noqa: E402


def page_index(pages):
    """Zwraca (lista liczników tf per strona, słownik idf)."""
    df = collections.Counter()
    tf_list = []
    for p in pages:
        tf = collections.Counter(toks(p['text']))
        tf_list.append(tf)
        df.update(tf.keys())
    n = len(pages)
    idf = {w: math.log(n / (1 + c)) for w, c in df.items()}
    return tf_list, idf


def top_pages_for(text, pages, tf_list, idf, k=8):
    """Indeksy k stron najbardziej związanych z podanym tekstem."""
    qtf = collections.Counter(toks(text))
    qvec = {w: (1 + math.log(c)) * idf.get(w, 0) for w, c in qtf.items() if w in idf}
    qnorm = math.sqrt(sum(v * v for v in qvec.values())) or 1
    scored = []
    for i, tf in enumerate(tf_list):
        pvec = {w: (1 + math.log(c)) * idf.get(w, 0) for w, c in tf.items()}
        pnorm = math.sqrt(sum(v * v for v in pvec.values())) or 1
        scored.append((sum(v * pvec[w] for w, v in qvec.items() if w in pvec) / (qnorm * pnorm), i))
    scored.sort(reverse=True)
    return [i for _, i in scored[:k]]


def group_items(items, pages, tf_list, idf, per_group=6, k=8):
    """Przypisuje każdemu pytaniu jego strony, potem skleja pytania w grupy o zbliżonym
    zestawie stron — dzięki temu suma stron w grupie rośnie wolniej niż liczba pytań."""
    for it in items:
        text = ' '.join([str(it.get('question') or '')] + [str(v or '') for v in (it.get('options') or {}).values()])
        it['_pages'] = set(top_pages_for(text, pages, tf_list, idf, k))

    remaining = list(items)
    groups = []
    while remaining:
        seed = remaining.pop(0)
        grp = [seed]
        union = set(seed['_pages'])
        remaining.sort(key=lambda x: -len(x['_pages'] & union))   # najpierw najbardziej pokrewne
        while remaining and len(grp) < per_group:
            cand = remaining[0]
            if len(union | cand['_pages']) > k * 3:               # nie pozwól grupie spuchnąć
                break
            grp.append(remaining.pop(0))
            union |= cand['_pages']
        groups.append({'items': grp, 'pages': sorted(union)})
    return groups


def render(pages, idx_list):
    out = []
    for i in idx_list:
        p = pages[i]
        out.append(f"## [str. książki {p['book']} | PDF {p['pdf']}]")
        out.append(p['text'])
        out.append("")
    return '\n'.join(out)
