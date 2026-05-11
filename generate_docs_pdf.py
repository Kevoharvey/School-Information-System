"""
Convert the Galala SIS database documentation markdown to a print-ready HTML file.
Open the resulting HTML in Chrome/Edge, then Ctrl+P -> Save as PDF.
"""
import markdown
import os

DOC_PATH = r"C:\Users\Youssef\.gemini\antigravity\brain\0aae80dc-93dd-48c5-98f3-534a8da2dfd3\db_documentation.md"
OUT_PATH = r"C:\Users\Youssef\OneDrive\Desktop\Galala_SIS_Database_Documentation.html"

with open(DOC_PATH, "r", encoding="utf-8") as f:
    md_text = f.read()

body_html = markdown.markdown(
    md_text,
    extensions=["tables", "fenced_code", "toc"],
)

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Galala SIS — Database & Query Documentation</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap');

  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: 'Inter', Arial, sans-serif;
    font-size: 13.5px;
    line-height: 1.7;
    color: #1a202c;
    background: #fff;
    padding: 40px 60px;
    max-width: 1000px;
    margin: 0 auto;
  }}

  /* Cover-style H1 */
  h1 {{
    font-size: 28px;
    font-weight: 700;
    color: #1e3a8a;
    border-bottom: 3px solid #2563eb;
    padding-bottom: 10px;
    margin: 32px 0 18px;
  }}
  h2 {{
    font-size: 20px;
    font-weight: 700;
    color: #1e40af;
    border-left: 4px solid #3b82f6;
    padding-left: 10px;
    margin: 28px 0 12px;
    page-break-before: always;
  }}
  h2:first-of-type {{ page-break-before: avoid; }}
  h3 {{
    font-size: 15px;
    font-weight: 700;
    color: #1e3a8a;
    margin: 22px 0 8px;
  }}
  h4 {{
    font-size: 13.5px;
    font-weight: 600;
    color: #374151;
    margin: 16px 0 6px;
  }}

  p {{ margin-bottom: 10px; }}

  /* Tables */
  table {{
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0 20px;
    font-size: 13px;
  }}
  th {{
    background: #1e40af;
    color: #fff;
    text-align: left;
    padding: 8px 12px;
    font-weight: 600;
  }}
  td {{
    padding: 7px 12px;
    border-bottom: 1px solid #e5e7eb;
    vertical-align: top;
  }}
  tr:nth-child(even) td {{ background: #f0f4ff; }}

  /* Code */
  pre {{
    background: #0f172a;
    color: #e2e8f0;
    border-radius: 8px;
    padding: 16px 18px;
    overflow-x: auto;
    margin: 12px 0 20px;
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 12px;
    line-height: 1.6;
    page-break-inside: avoid;
  }}
  code {{
    font-family: 'JetBrains Mono', 'Courier New', monospace;
    font-size: 12px;
    background: #e0e7ff;
    color: #1e40af;
    padding: 1px 5px;
    border-radius: 4px;
  }}
  pre code {{
    background: none;
    color: inherit;
    padding: 0;
    border-radius: 0;
  }}

  blockquote {{
    border-left: 3px solid #60a5fa;
    margin: 12px 0;
    padding: 8px 14px;
    background: #eff6ff;
    color: #1e40af;
    border-radius: 0 6px 6px 0;
    font-size: 13px;
  }}

  hr {{
    border: none;
    border-top: 1px solid #e5e7eb;
    margin: 30px 0;
  }}

  ul, ol {{
    padding-left: 22px;
    margin-bottom: 10px;
  }}
  li {{ margin-bottom: 4px; }}

  /* Print settings */
  @media print {{
    body {{ padding: 20px 30px; font-size: 12px; }}
    h2 {{ page-break-before: always; }}
    pre {{ page-break-inside: avoid; }}
    table {{ page-break-inside: avoid; }}
  }}
</style>
</head>
<body>
<!-- Cover header -->
<div style="text-align:center; padding: 40px 0 30px; border-bottom: 2px solid #2563eb; margin-bottom: 36px;">
  <div style="font-size:13px; color:#6b7280; text-transform:uppercase; letter-spacing:2px; margin-bottom:8px;">Galala International School</div>
  <h1 style="border:none; padding:0; margin:0; font-size:32px;">School Information System</h1>
  <div style="font-size:18px; color:#2563eb; font-weight:600; margin-top:8px;">Database & Query Documentation</div>
  <div style="margin-top:16px; font-size:12px; color:#9ca3af;">Generated May 2026</div>
</div>

{body_html}
</body>
</html>"""

with open(OUT_PATH, "w", encoding="utf-8") as f:
    f.write(HTML)

print(f"Done! File saved to:\n{OUT_PATH}")
print("\nTo create a PDF:")
print("1. Open the HTML file in Chrome or Edge")
print("2. Press Ctrl+P")
print("3. Set 'Destination' to 'Save as PDF'")
print("4. Enable 'Background graphics' in More settings")
print("5. Click Save")
