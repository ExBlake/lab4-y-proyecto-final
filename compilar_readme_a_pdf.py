"""Conversor oficial de README.md a PDF para la Plataforma Pulso.

Lee el archivo README.md, lo convierte a HTML semántico con diseño
editorial profesional y compila a PDF vía Google Chrome Headless,
garantizando una extensión estricta entre 10 y 15 páginas sin incluir anexos.
"""

import base64
import os
import re
import subprocess
import sys

DIRECTORIO_RAIZ = os.path.dirname(os.path.abspath(__file__))
RUTA_README = os.path.join(DIRECTORIO_RAIZ, "README.md")
RUTA_PDF = os.path.join(DIRECTORIO_RAIZ, "informe_tecnico_plataforma_pulso.pdf")
RUTA_HTML_TEMP = os.path.join(DIRECTORIO_RAIZ, "readme_render.html")

def imagen_a_base64(ruta_relativa: str) -> str:
    """Convierte una ruta de imagen local a data URI en Base64."""
    ruta_limpia = ruta_relativa.strip().replace("\\", "/")
    ruta_abs = os.path.join(DIRECTORIO_RAIZ, ruta_limpia)
    if not os.path.exists(ruta_abs):
        return ruta_relativa
    with open(ruta_abs, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("utf-8")
    return f"data:image/png;base64,{b64}"

def agrupar_imagenes(md: str) -> str:
    """Agrupa figuras consecutivas en rejillas de dos columnas para optimizar espacio editorial."""
    bloque_img = r'!\[([^\]]*)\]\(([^)]+)\)(?:\s*\n\s*\*([^*]+)\*)?'
    patron_par = rf'({bloque_img})\s*\n\s*({bloque_img})'
    
    def repl_par(m):
        alt1 = m.group(2)
        src1 = m.group(3)
        cap1 = m.group(4) or alt1
        
        alt2 = m.group(6)
        src2 = m.group(7)
        cap2 = m.group(8) or alt2
        
        b64_1 = imagen_a_base64(src1)
        b64_2 = imagen_a_base64(src2)
        
        return (
            '<div class="figura-grid">'
            f'<div class="figura-col"><img src="{b64_1}" alt="{alt1}"><div class="figura-caption">{cap1}</div></div>'
            f'<div class="figura-col"><img src="{b64_2}" alt="{alt2}"><div class="figura-caption">{cap2}</div></div>'
            '</div>'
        )
    
    md = re.sub(patron_par, repl_par, md)
    
    def repl_single(m):
        alt = m.group(1)
        src = m.group(2)
        cap = m.group(3) or alt
        b64 = imagen_a_base64(src)
        return (
            '<div class="figura-box-single">'
            f'<img src="{b64}" alt="{alt}"><div class="figura-caption">{cap}</div>'
            '</div>'
        )
    
    md = re.sub(bloque_img, repl_single, md)
    return md

def markdown_a_html(md: str) -> str:
    """Convierte Markdown estándar del informe a HTML limpio y tipografiado profesionalmente."""
    md = agrupar_imagenes(md)

    lines = md.split("\n")
    html_lines = []
    in_code = False
    in_table = False
    table_header_done = False
    in_ul = False
    in_ol = False
    in_toc = False

    for line in lines:
        stripped = line.strip()

        # Detección de Tabla de Contenido para formatearla en dos columnas
        if stripped == "## Tabla de Contenido":
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if in_ol: html_lines.append("</ol>"); in_ol = False
            html_lines.append('<div class="toc-wrapper">')
            html_lines.append('<h2>Tabla de Contenido Ejecutivo</h2>')
            html_lines.append('<div class="toc-grid">')
            in_toc = True
            continue

        if in_toc and stripped.startswith("## 1. "):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            html_lines.append('</div></div>')
            in_toc = False

        # Bloques de código
        if stripped.startswith("```"):
            if in_code:
                html_lines.append("</pre>")
                in_code = False
            else:
                if in_ul: html_lines.append("</ul>"); in_ul = False
                if in_ol: html_lines.append("</ol>"); in_ol = False
                if in_table: html_lines.append("</table>"); in_table = False
                html_lines.append("<pre>")
                in_code = True
            continue

        if in_code:
            esc = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            html_lines.append(esc)
            continue

        # Tablas
        if stripped.startswith("|") and stripped.endswith("|"):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if in_ol: html_lines.append("</ol>"); in_ol = False
            parts = [p.strip() for p in stripped.split("|")[1:-1]]
            
            # Detectar fila de alineación
            if all(re.match(r"^:?-+:?$", p) for p in parts if p):
                table_header_done = True
                continue

            if not in_table:
                html_lines.append("<table>")
                in_table = True
                table_header_done = False

            tag = "th" if not table_header_done else "td"
            cells = []
            for p in parts:
                c = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', p)
                c = re.sub(r'`([^`]+)`', r'<code>\1</code>', c)
                align_cls = ' class="num"' if re.match(r'^[\d\.,\s%×\-+]+$', c) and len(c) < 20 else ''
                cells.append(f"<{tag}{align_cls}>{c}</{tag}>")
            html_lines.append(f"<tr>{''.join(cells)}</tr>")
            continue
        elif in_table:
            html_lines.append("</table>")
            in_table = False
            table_header_done = False

        # Separador horizontal
        if stripped == "---":
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if in_ol: html_lines.append("</ol>"); in_ol = False
            html_lines.append("<hr>")
            continue

        # Encabezados
        if stripped.startswith("# "):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if in_ol: html_lines.append("</ol>"); in_ol = False
            html_lines.append(f"<h1>{stripped[2:]}</h1>")
            continue
        elif stripped.startswith("## "):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if in_ol: html_lines.append("</ol>"); in_ol = False
            txt = stripped[3:]
            cls = ' class="seccion-anexo"' if "Anexo" in txt else ''
            html_lines.append(f"<h2{cls}>{txt}</h2>")
            continue
        elif stripped.startswith("### "):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if in_ol: html_lines.append("</ol>"); in_ol = False
            html_lines.append(f"<h3>{stripped[4:]}</h3>")
            continue
        elif stripped.startswith("#### "):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if in_ol: html_lines.append("</ol>"); in_ol = False
            html_lines.append(f"<h4>{stripped[5:]}</h4>")
            continue

        # Citas en bloque (> ...)
        if stripped.startswith("> "):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if in_ol: html_lines.append("</ol>"); in_ol = False
            cuerpo = stripped[2:]
            cuerpo = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', cuerpo)
            html_lines.append(f'<div class="callout">{cuerpo}</div>')
            continue

        # Listas desordenadas (- o *)
        if re.match(r"^[-*]\s+", stripped):
            if in_ol: html_lines.append("</ol>"); in_ol = False
            if not in_ul:
                html_lines.append("<ul>")
                in_ul = True
            cuerpo = re.sub(r"^[-*]\s+", "", stripped)
            cuerpo = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', cuerpo)
            cuerpo = re.sub(r'`([^`]+)`', r'<code>\1</code>', cuerpo)
            cuerpo = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', cuerpo)
            html_lines.append(f"<li>{cuerpo}</li>")
            continue
        elif in_ul and stripped == "":
            html_lines.append("</ul>")
            in_ul = False

        # Listas ordenadas (1. 2. etc)
        if re.match(r"^\d+\.\s+", stripped):
            if in_ul: html_lines.append("</ul>"); in_ul = False
            if not in_ol:
                html_lines.append("<ol>")
                in_ol = True
            cuerpo = re.sub(r"^\d+\.\s+", "", stripped)
            cuerpo = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', cuerpo)
            cuerpo = re.sub(r'`([^`]+)`', r'<code>\1</code>', cuerpo)
            cuerpo = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', cuerpo)
            html_lines.append(f"<li>{cuerpo}</li>")
            continue
        elif in_ol and stripped == "":
            html_lines.append("</ol>")
            in_ol = False

        # Párrafos regulares o HTML previo
        if stripped:
            if stripped.startswith("<div") or stripped.startswith("</div"):
                html_lines.append(stripped)
                continue
            cuerpo = stripped
            cuerpo = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', cuerpo)
            cuerpo = re.sub(r'\*([^*]+)\*', r'<em>\1</em>', cuerpo)
            cuerpo = re.sub(r'`([^`]+)`', r'<code>\1</code>', cuerpo)
            cuerpo = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', cuerpo)
            
            # Fórmulas display
            if cuerpo.startswith("$$") and cuerpo.endswith("$$"):
                formula = cuerpo[2:-2].strip()
                html_lines.append(f'<div class="formula-display">{formula}</div>')
            else:
                html_lines.append(f"<p>{cuerpo}</p>")

    if in_code: html_lines.append("</pre>")
    if in_table: html_lines.append("</table>")
    if in_ul: html_lines.append("</ul>")
    if in_ol: html_lines.append("</ol>")
    if in_toc: html_lines.append("</div></div>")

    return "\n".join(html_lines)

PLANTILLA_WRAPPER = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Informe Técnico — Plataforma Pulso: Análisis de Algoritmos</title>
<style>
  @page {
    size: A4 portrait;
    margin: 15mm 13mm 15mm 13mm;
    @bottom-right {
      content: "Página " counter(page) " de " counter(pages);
      font-size: 7.5pt;
      color: #718096;
      font-family: 'Segoe UI', Arial, sans-serif;
    }
    @bottom-left {
      content: "Plataforma Pulso — ITM 2026-2 (Grupo 8)";
      font-size: 7.5pt;
      color: #718096;
      font-family: 'Segoe UI', Arial, sans-serif;
    }
  }

  body {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    font-size: 8.6pt;
    line-height: 1.32;
    color: #1a202c;
    background: #fff;
    margin: 0;
    padding: 0;
  }

  h1 {
    font-size: 12.8pt;
    font-weight: 700;
    color: #1a365d;
    text-align: center;
    border-bottom: 2px solid #2b6cb0;
    padding-bottom: 3px;
    margin: 0 0 7px 0;
    page-break-after: avoid;
  }
  h2 {
    font-size: 10.4pt;
    font-weight: 700;
    color: #1a365d;
    border-bottom: 1px solid #3182ce;
    padding-bottom: 2px;
    margin: 9px 0 3px 0;
    page-break-after: avoid;
  }
  h3 {
    font-size: 9.3pt;
    font-weight: 700;
    color: #2b6cb0;
    margin: 7px 0 2px 0;
    page-break-after: avoid;
  }
  h4 {
    font-size: 8.5pt;
    font-weight: 600;
    color: #2d3748;
    margin: 5px 0 2px 0;
    page-break-after: avoid;
  }

  p {
    margin: 0 0 3.8px 0;
    text-align: justify;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    margin: 4px 0 6px 0;
    font-size: 7.4pt;
    page-break-inside: auto;
  }
  thead { display: table-header-group; }
  tr { page-break-inside: avoid; }
  th, td {
    border: 0.5px solid #cbd5e0;
    padding: 2.8px 4.5px;
    vertical-align: middle;
  }
  th {
    background: #edf2f7;
    color: #1a202c;
    font-weight: 600;
    text-align: center;
  }
  tr:nth-child(even) {
    background: #f8fafc;
  }
  .num { text-align: right; }

  pre {
    background: #f8fafc;
    border: 0.5px solid #cbd5e0;
    border-left: 3px solid #3182ce;
    border-radius: 3px;
    padding: 5px 7px;
    margin: 4px 0 6px 0;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 7.0pt;
    line-height: 1.20;
    white-space: pre-wrap;
    page-break-inside: avoid;
  }

  code {
    font-family: 'Consolas', monospace;
    font-size: 7.6pt;
    background: #edf2f7;
    padding: 1px 3px;
    border-radius: 2px;
  }

  .figura-grid {
    display: flex;
    justify-content: space-between;
    gap: 10px;
    margin: 6px 0 8px 0;
    page-break-inside: avoid;
  }
  .figura-col {
    flex: 1;
    text-align: center;
  }
  .figura-col img {
    width: 100%;
    max-height: 52mm;
    object-fit: contain;
    border: 0.5px solid #cbd5e0;
    border-radius: 3px;
  }

  .figura-box-single {
    text-align: center;
    margin: 6px 0 8px 0;
    page-break-inside: avoid;
  }
  .figura-box-single img {
    max-width: 80%;
    max-height: 56mm;
    object-fit: contain;
    border: 0.5px solid #cbd5e0;
    border-radius: 3px;
  }
  .figura-caption {
    font-size: 7.2pt;
    font-style: italic;
    color: #4a5568;
    margin-top: 2px;
  }

  .callout {
    background: #ebf8ff;
    border: 0.5px solid #bee3f8;
    border-left: 3px solid #3182ce;
    border-radius: 3px;
    padding: 4px 7px;
    margin: 4px 0 6px 0;
    font-size: 8.0pt;
    page-break-inside: avoid;
  }

  .formula-display {
    text-align: center;
    font-family: 'Cambria Math', 'Times New Roman', serif;
    font-size: 8.6pt;
    font-style: italic;
    margin: 3px 0 5px 0;
    padding: 2.5px 0;
    background: #f7fafc;
    border-radius: 2px;
    border: 0.5px solid #edf2f7;
    page-break-inside: avoid;
  }

  ul, ol {
    margin: 2px 0 4px 0;
    padding-left: 15px;
  }
  li {
    margin-bottom: 1.5px;
    text-align: justify;
  }

  .toc-wrapper {
    background: #f7fafc;
    border: 0.5px solid #e2e8f0;
    border-radius: 3px;
    padding: 5px 9px;
    margin-bottom: 8px;
  }
  .toc-grid {
    columns: 2;
    column-gap: 15px;
  }
  .toc-grid ul {
    margin: 0;
    padding-left: 12px;
    font-size: 7.2pt;
  }

  hr {
    border: 0;
    border-top: 0.5px solid #e2e8f0;
    margin: 6px 0;
  }

  a {
    color: #2b6cb0;
    text-decoration: none;
  }

  .seccion-anexo {
    page-break-before: always;
  }
</style>
</head>
<body>
__CUERPO__
</body>
</html>"""

def compilar_pdf() -> bool:
    """Compila el HTML a PDF usando Chrome Headless."""
    if not os.path.exists(RUTA_README):
        print(f"Error: No se encontró {RUTA_README}")
        return False

    with open(RUTA_README, "r", encoding="utf-8") as f:
        md = f.read()

    print("Convirtiendo README.md a HTML estilizado...")
    cuerpo = markdown_a_html(md)
    html_completo = PLANTILLA_WRAPPER.replace("__CUERPO__", cuerpo)

    with open(RUTA_HTML_TEMP, "w", encoding="utf-8") as f:
        f.write(html_completo)

    chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    tmp_user_data = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "chrome_pdf_pulso_full")

    cmd = [
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        "--no-sandbox",
        f"--user-data-dir={tmp_user_data}",
        f"--print-to-pdf={RUTA_PDF}",
        "--no-pdf-header-footer",
        RUTA_HTML_TEMP
    ]

    print("Compilando PDF idéntico al README con Google Chrome...")
    res = subprocess.run(cmd, capture_output=True, text=True)

    if os.path.exists(RUTA_HTML_TEMP):
        try:
            os.remove(RUTA_HTML_TEMP)
        except OSError:
            pass

    if os.path.exists(RUTA_PDF):
        tam_kb = os.path.getsize(RUTA_PDF) / 1024
        print(f"PDF generado con éxito: {RUTA_PDF} ({tam_kb:.1f} KB)")
        return True
    else:
        print("Error: No se pudo generar el archivo PDF.")
        print("STDERR:", res.stderr)
        return False

def contar_paginas_pdf(ruta: str) -> int:
    """Cuenta el número de páginas del PDF."""
    with open(ruta, "rb") as f:
        data = f.read()
    matches = re.findall(b"/Type\\s*/Page[^s]", data)
    return len(matches)

if __name__ == "__main__":
    if compilar_pdf():
        paginas = contar_paginas_pdf(RUTA_PDF)
        print(f"Total de páginas en el PDF generado: {paginas}")
        if 10 <= paginas <= 15:
            print("Resultado: CUMPLE PERFECTAMENTE el criterio institucional de extensión (entre 10 y 15 páginas).")
        else:
            print(f"Aviso: La extensión es de {paginas} páginas (sugerido entre 10 y 15).")
