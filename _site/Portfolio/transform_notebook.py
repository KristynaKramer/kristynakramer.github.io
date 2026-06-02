"""
transform_notebook.py

Transforms a Jupyter-exported HTML file for use in a Jekyll site.

Usage:
    python transform_notebook.py input.html output.html "Page Title"

Example:
    python transform_notebook.py export.html 01-USMedicalInsurance.html "Data | Portfolio"

Changes applied:
    1. Adds Jekyll front matter
    2. Adds font and width overrides scoped to .jp-notebook-wrapper
    3. Removes structural tags (<!DOCTYPE>, <html>, <head>, <body>, <title>, etc.)
    4. Replaces <body> with a scoped wrapper <div>
    5. Replaces Jupyter's <main> with a <div> to avoid nesting conflicts
    6. Scopes global CSS selectors (body, a, pre) to .jp-notebook-wrapper
    7. Fixes TOC anchor link case mismatches

TOC link fixes:
    Edit the TOC_FIXES dictionary below if your notebook has different headings.
    Keys are the href values Jupyter generates (lowercase, hyphenated).
    Values are the actual heading IDs Jupyter assigns.
    Run the script once and check the browser console if links still don't work.
"""

import re
import sys
from pathlib import Path


# ── Configuration ────────────────────────────────────────────────────────────

FONT_OVERRIDE = """\
<style>
.jp-notebook-wrapper {
    --jp-ui-font-size1: 1.125rem;
    --jp-content-font-size1: 1.125rem;
    --jp-ui-font-family: "Calibri", "Carlito", sans-serif;
    --jp-content-font-family: "Calibri", "Carlito", sans-serif;
    --jp-code-font-size: 1rem;
    max-width: min(75ch, 800px);
}
@media (max-width: 768px) {
    .jp-notebook-wrapper {
        max-width: 100%;
        padding: 0 1rem;
    }
}
</style>

"""

# Edit these to match your notebook's headings.
# Key:   the lowercase href Jupyter writes in the TOC
# Value: the actual id Jupyter puts on the heading element
TOC_FIXES = {
    '#dataset-overview':                      '#Dataset-overview',
    '#exploring-the-diversity-of-the-data':   '#Exploring-the-diversity-of-the-data',
    '#what-influences-the-cost-of-medical-insurance': '#What-influences-the-cost-of-medical-insurance?',
    '#age':                                   '#Age',
    '#sex':                                   '#Sex',
    '#smoking':                               '#Smoking',
    '#bmi':                                   '#BMI',
    '#number-of-children':                    '#Number-of-kids',
    '#correlations':                          '#Correlations',
    '#conclusion':                            '#Conclusion',
}


# ── Transformation ───────────────────────────────────────────────────────────

def transform(content: str, title: str) -> str:

    # 1. Normalise line endings
    content = content.replace('\r\n', '\n')

    # 2. Front matter + font override
    front_matter = f'---\nlayout: default\ntitle: "{title}"\n---\n\n'
    content = front_matter + FONT_OVERRIDE + content

    # 3. Remove <!DOCTYPE html>
    content = re.sub(r'<!DOCTYPE html>\n\n?', '', content, count=1)

    # 4. Remove commented-out <html>/<head> fragment (older exports)
    content = re.sub(r'<!-- <html lang="en">.*?-->\n\n?', '', content, count=1, flags=re.DOTALL)

    # 5. Remove real <html> tag (newer exports)
    content = re.sub(r'<html[^>]*>\n', '', content, count=1)

    # 6. Remove <head>...</head> opening line (meta tags, no closing tag yet)
    content = re.sub(r'<head>[^\n]*\n(<meta[^\n]*\n)*', '', content, count=1)

    # 7. Remove <title>...</title> (may have a <script> on the same line)
    content = re.sub(r'<title>[^<]*</title>(<script[^>]*></script>)?\n', '', content, count=1)

    # 8. Remove </head>
    content = re.sub(r'</head>\n', '', content, count=1)
    content = content.replace('<!-- End of mermaid configuration --></head>\n',
                              '<!-- End of mermaid configuration -->\n', 1)

    # 9. Replace <body ...> with scoped wrapper div
    content = re.sub(
        r'<body[^>]*>',
        '<div class="jp-notebook-wrapper jp-Notebook" data-jp-theme-light="true" data-jp-theme-name="JupyterLab Light">',
        content, count=1
    )

    # 10. Replace Jupyter's <main> with a plain div
    content = re.sub(r'\n<main>\n', '\n<div class="jp-notebook-main">\n', content, count=1)
    content = re.sub(r'\n</main>\n', '\n</div>\n', content, count=1)

    # 11. Replace </body>\n</html> with closing wrapper div
    content = re.sub(r'</body>\n</html>\n?$', '</div>\n', content)

    # 12. Scope `body { ... }` to wrapper
    content = content.replace(
        'body {\n  color: var(--jp-ui-font-color1);\n  font-size: var(--jp-ui-font-size1);\n}',
        '.jp-notebook-wrapper {\n  color: var(--jp-ui-font-color1);\n  font-size: var(--jp-ui-font-size1);\n}'
    )

    # 13. Scope global `a` and `a:hover` to wrapper
    content = content.replace(
        '/* Disable native link decoration styles everywhere outside of dialog boxes */\n'
        'a {\n  text-decoration: unset;\n  color: unset;\n}\n\n'
        'a:hover {\n  text-decoration: unset;\n  color: unset;\n}',
        '/* Disable native link decoration styles everywhere outside of dialog boxes */\n'
        '.jp-notebook-wrapper a {\n  text-decoration: unset;\n  color: unset;\n}\n\n'
        '.jp-notebook-wrapper a:hover {\n  text-decoration: unset;\n  color: unset;\n}'
    )

    # 14. Scope global `pre { line-height }` to wrapper
    content = re.sub(
        r'( {4})pre \{ line-height',
        r'\1.jp-notebook-wrapper pre { line-height',
        content, count=1
    )

    # 15. Fix TOC anchor link case mismatches
    for wrong, correct in TOC_FIXES.items():
        content = content.replace(f'href="{wrong}"', f'href="{correct}"')

    return content


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) != 4:
        print("Usage: python transform_notebook.py input.html output.html \"Page Title\"")
        sys.exit(1)

    input_path  = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    title       = sys.argv[3]

    if not input_path.exists():
        print(f"Error: {input_path} not found.")
        sys.exit(1)

    content = input_path.read_bytes().decode('utf-8')
    content = transform(content, title)
    output_path.write_text(content, encoding='utf-8')
    print(f"Done: {output_path}")


if __name__ == '__main__':
    main()
