# -*- coding: utf-8 -*-
"""Przygotowuje paczkę wzbogacania ubogich wyjaśnień dla jednego działu.

Ubogie = jednozdaniowe i nieodnoszące się do żadnej błędnej odpowiedzi. Klucz jest poprawny,
zmieniamy wyłącznie kolumnę Wyjaśnienie.

Użycie: python3 scripts/validation/prepare_enrich.py <numer działu>
"""
import collections
import json
import os
import sys

import openpyxl

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
WORK = os.environ.get('NEURO_WORK_DIR') or os.path.join(REPO, '.validation-work')
OUTD = os.path.join(REPO, 'docs', 'validation', 'enriched')
sys.path.insert(0, HERE)


def main(section_id):
    from build_dossiers import load_pages
    from build_question_dossiers import page_index, top_pages_for, render

    thin = json.load(open(os.path.join(WORK, 'thin-explanations.json')))
    sheets = {sh: rows for sh, rows in thin.items() if int(sh.split('.')[0]) == section_id}
    if not sheets:
        sys.exit(f'brak ubogich wyjaśnień w dziale {section_id}')

    wb = openpyxl.load_workbook(os.path.join(REPO, 'data', 'neuro_questions.xlsx'), read_only=True)
    pages = load_pages()
    tf, idf = page_index(pages)
    os.makedirs(OUTD, exist_ok=True)
    td = os.path.join(WORK, f'enrich-{section_id}')
    os.makedirs(td, exist_ok=True)

    manifest = []
    for sh, rows in sorted(sheets.items()):
        ws = wb[sh]
        by_row = {i: r for i, r in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2)}
        items, pageset = [], set()
        for row in rows:
            # preflight: pomiń, jeśli wynik już istnieje
            if os.path.exists(os.path.join(OUTD, f'{sh}-{row}.json'.replace('/', '_'))):
                continue
            r = by_row[row]
            opts = {k: r[2 + j] for j, k in enumerate('ABCD')}
            items.append({'row': row, 'id': str(r[0]), 'question': r[1], 'options': opts,
                          'correct': r[6], 'oldExplanation': r[7]})
            text = ' '.join([str(r[1] or '')] + [str(v or '') for v in opts.values()])
            pageset.update(top_pages_for(text, pages, tf, idf, k=3))
        if not items:
            continue
        slug = sh.replace('.', '-').replace(' ', '-').replace('/', '_')
        json.dump({'sheet': sh, 'count': len(items), 'items': items},
                  open(os.path.join(td, f'{slug}.json'), 'w'), ensure_ascii=False, indent=1)
        open(os.path.join(td, f'dossier-{slug}.md'), 'w').write(
            f'# Wycinki podręcznika dla arkusza {sh}\n\n' + render(pages, sorted(pageset)))
        manifest.append({'sheet': sh, 'slug': slug, 'task': f'enrich-{section_id}/{slug}.json',
                         'dossier': f'enrich-{section_id}/dossier-{slug}.md', 'count': len(items),
                         'pages': len(pageset)})

    json.dump(manifest, open(os.path.join(WORK, f'enrich-{section_id}-manifest.json'), 'w'),
              ensure_ascii=False, indent=1)
    total = sum(m['count'] for m in manifest)
    print(f'dział {section_id}: {total} pytań w {len(manifest)} arkuszach')
    for m in manifest:
        print(f"  {m['sheet']:34} {m['count']:>3} pytań, {m['pages']} stron źródła")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit('Użycie: python3 scripts/validation/prepare_enrich.py <numer działu>')
    main(int(sys.argv[1]))
