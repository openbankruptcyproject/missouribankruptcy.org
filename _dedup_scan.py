#!/usr/bin/env python3
"""Scan root English pages for Missouri-specific substance.

Signals of Missouri-specific content (any one counts):
  - "Missouri" / "MO.bar" / "RSMo" / "MoRS" / Missouri statute numbers
  - Specific MO people/places: Norton, Fenimore, Fink, Daugherty,
    Kansas City, St. Louis, Springfield, Jefferson City, Columbia, Joplin
  - W.D. Mo. / E.D. Mo. / Missouri Western / Missouri Eastern
  - Missouri counties: Jackson, Greene, Boone, Clay, Platte, ...
  - RSMo chapter numbers like 513., 407., 516., 525.

Reports:
  - Word count
  - MO-specific token count
  - Thin-content candidates (low words + low MO tokens)
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent

MO_PATTERNS = [
    r'\bMissouri\b',
    r'\bRSMo\b',
    r'\bMO\.?\s*Rev',
    r'\bW\.?D\.?\s*Mo\b',
    r'\bE\.?D\.?\s*Mo\b',
    r'\bNorton\b',
    r'\bFenimore\b',
    r'\bFink\b',
    r'\bDaugherty\b',
    r'\bKansas City\b',
    r'\bSt\.?\s*Louis\b',
    r'\bSpringfield\b',
    r'\bJefferson City\b',
    r'\bColumbia\b',
    r'\bJoplin\b',
    r'\bMobar\b',
    r'\bMO Bar\b',
    r'\b(Jackson|Greene|Boone|Clay|Platte|Cole|Jasper|Buchanan|St\.\s*Charles|Franklin|Cass|Taney|Christian) County\b',
    r'\b513\.\d+\b',  # exemptions
    r'\b516\.\d+\b',  # SOL
    r'\b407\.\d+\b',  # MMPA
    r'\b525\.\d+\b',  # garnishment
    r'\b452\.\d+\b',  # dissolution
]
MO_RE = re.compile('|'.join(MO_PATTERNS), re.IGNORECASE)

TAG_RE = re.compile(r'<[^>]+>')
WS_RE = re.compile(r'\s+')


def analyze(path: Path) -> dict:
    html = path.read_text(encoding='utf-8', errors='ignore')
    # Strip nav, footer, subnav, schema JSON-LD to not inflate MO hits
    stripped = re.sub(r'<nav.*?</nav>', '', html, flags=re.DOTALL)
    stripped = re.sub(r'<footer.*?</footer>', '', stripped, flags=re.DOTALL)
    stripped = re.sub(r'<!-- SUBNAV:START -->.*?<!-- SUBNAV:END -->', '', stripped, flags=re.DOTALL)
    stripped = re.sub(r'<script.*?</script>', '', stripped, flags=re.DOTALL)
    stripped = re.sub(r'<style.*?</style>', '', stripped, flags=re.DOTALL)
    text = TAG_RE.sub(' ', stripped)
    text = WS_RE.sub(' ', text).strip()
    words = len(text.split())
    mo_hits = len(MO_RE.findall(text))
    return {
        'file': path.name,
        'words': words,
        'mo_hits': mo_hits,
        'mo_per_1k': round(mo_hits / max(words, 1) * 1000, 1),
    }


def main():
    files = sorted(p for p in ROOT.glob('*.html') if not p.name.endswith('-es.html'))
    rows = [analyze(p) for p in files]
    rows.sort(key=lambda r: (r['mo_hits'], r['mo_per_1k'], r['words']))

    print(f"{'file':<38} {'words':>7} {'MO hits':>8} {'/1k':>6}")
    print('-' * 62)
    for r in rows:
        print(f"{r['file']:<38} {r['words']:>7} {r['mo_hits']:>8} {r['mo_per_1k']:>6}")

    print()
    # Thin candidates: <5 MO hits OR <800 words with <10 MO hits
    thin = [r for r in rows if r['mo_hits'] < 5 or (r['words'] < 800 and r['mo_hits'] < 10)]
    print(f"\nTHIN-CONTENT CANDIDATES ({len(thin)}):")
    for r in thin:
        print(f"  - {r['file']} ({r['words']}w, {r['mo_hits']} MO hits)")


if __name__ == '__main__':
    main()
