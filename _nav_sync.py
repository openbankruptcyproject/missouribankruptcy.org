#!/usr/bin/env python3
"""One-off: sync top nav across root-level English pages to canonical layout.
Also injects a footer sub-nav linking the 6 deeper substantive pages.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent

CANONICAL_LINKS = (
    '<div class="links">'
    '<a href="/">Home</a>'
    '<a href="districts.html">Districts</a>'
    '<a href="income-limits.html">Means Test</a>'
    '<a href="exemptions.html">Exemptions</a>'
    '<a href="trustees.html">Trustees</a>'
    '<a href="legal-aid.html">Legal Aid</a>'
    '<a href="case-law.html">Case Law</a>'
    '<a href="resources.html">Resources</a>'
    '<a href="https://openbankruptcyproject.org">OBP</a>'
    '</div>'
)

FOOTER_SUBNAV = (
    '<!-- SUBNAV:START -->'
    '<nav class="subnav" aria-label="Deep content" style="background:#0d1117;border-top:1px solid #30363d;padding:1rem 0;margin-top:2rem">'
    '<div class="container" style="max-width:1200px;margin:0 auto;padding:0 1rem;text-align:center;font-size:0.9rem">'
    '<span style="color:#7d8590;margin-right:0.5rem">More Missouri law:</span>'
    '<a href="/legal-aid.html" style="color:#58a6ff;margin:0 0.6rem;text-decoration:none">Legal Aid</a>'
    '<a href="/filing-practice.html" style="color:#58a6ff;margin:0 0.6rem;text-decoration:none">Filing Practice</a>'
    '<a href="/case-law.html" style="color:#58a6ff;margin:0 0.6rem;text-decoration:none">Case Law</a>'
    '<a href="/debt-collection-law.html" style="color:#58a6ff;margin:0 0.6rem;text-decoration:none">Debt Collection</a>'
    '<a href="/primary-sources.html" style="color:#58a6ff;margin:0 0.6rem;text-decoration:none">Primary Sources</a>'
    '</div>'
    '</nav>'
    '<!-- SUBNAV:END -->'
)

# Match top nav link-block precisely: inside <nav> ... <div class="container">
# Tolerates:
#   - <nav>  OR  <nav aria-label="Main navigation">
#   - <a class="brand" href="/">  OR  <a href="/" class="brand">
# Anchors after `Missouri Bankruptcy Guide</a>` up to `</div></div></nav>`
TOPNAV_RE = re.compile(
    r'(<nav(?:\s+aria-label="[^"]+")?><div class="container">'
    r'<a (?:class="brand" href="/"|href="/" class="brand")>Missouri Bankruptcy Guide</a>)'
    r'<div class="links">.*?</div>'
    r'(</div></nav>)',
    re.DOTALL,
)

SKIP_FILES = {
    'about.html',           # different nav template (legal page)
    'privacy.html',         # different nav template (legal page)
    'es.html',              # Spanish landing, separate nav system
    'google1ddf9121b1b7e6ef.html',  # Search Console verification stub
}

SUBNAV_RE = re.compile(r'<!-- SUBNAV:START -->.*?<!-- SUBNAV:END -->', re.DOTALL)


def process(path: Path, dry_run: bool) -> tuple[bool, bool]:
    text = path.read_text(encoding='utf-8')
    orig = text

    new_text, n_top = TOPNAV_RE.subn(r'\1' + CANONICAL_LINKS + r'\2', text, count=1)

    # Inject footer subnav just before </main> (if present) or before <footer>.
    had_sub = bool(SUBNAV_RE.search(new_text))
    if had_sub:
        new_text = SUBNAV_RE.sub(FOOTER_SUBNAV, new_text)
        sub_changed = True
    else:
        # Try </main> first, then <footer
        if '</main>' in new_text:
            new_text = new_text.replace('</main>', FOOTER_SUBNAV + '</main>', 1)
            sub_changed = True
        elif re.search(r'<footer[\s>]', new_text):
            new_text = re.sub(r'(<footer[\s>])', FOOTER_SUBNAV + r'\1', new_text, count=1)
            sub_changed = True
        else:
            sub_changed = False

    changed = new_text != orig
    top_changed = n_top > 0

    if changed and not dry_run:
        path.write_text(new_text, encoding='utf-8')
    return top_changed, sub_changed


def main():
    dry = '--apply' not in sys.argv
    targets = sorted(
        p for p in ROOT.glob('*.html')
        if not p.name.endswith('-es.html') and p.name not in SKIP_FILES
    )
    total_top = total_sub = 0
    skipped = []
    for p in targets:
        top, sub = process(p, dry_run=dry)
        if top:
            total_top += 1
        if sub:
            total_sub += 1
        if not top:
            skipped.append(p.name)
    print(f"Mode: {'APPLY' if not dry else 'DRY-RUN'}")
    print(f"Files scanned: {len(targets)}")
    print(f"Top-nav replaced: {total_top}")
    print(f"Sub-nav injected/updated: {total_sub}")
    if skipped:
        print(f"Top-nav NOT matched in {len(skipped)} file(s):")
        for s in skipped:
            print(f"  - {s}")


if __name__ == '__main__':
    main()
