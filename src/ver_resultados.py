"""
ver_resultados.py
Visor HTML interactivo para los XMLs de resultados XQuery.
Uso: python ver_resultados.py
"""

import os, glob, html, xml.dom.minidom, webbrowser, tempfile

RESULTADOS_DIR = os.path.join(os.path.dirname(__file__), "resultados")

def load_xml(path):
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"<error>{e}</error>"

def main():
    files = sorted(glob.glob(os.path.join(RESULTADOS_DIR, "*.xml")))
    if not files:
        print(f"No se encontraron XMLs en: {RESULTADOS_DIR}")
        return

    # Embed each XML as a JS string
    js_files = []
    for path in files:
        name = os.path.basename(path)
        raw = load_xml(path)
        escaped = raw.replace("\\", "\\\\").replace("`", "\\`")
        js_files.append(f'{{ name: `{name}`, xml: `{escaped}` }}')

    js_data = ",\n".join(js_files)

    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Resultados XQuery — Yahoo Answers</title>
<style>
  :root {{
    --bg: #0d1117; --surface: #161b22; --border: #30363d;
    --blue: #58a6ff; --green: #3fb950; --orange: #d29922;
    --red: #f85149; --purple: #bc8cff; --text: #c9d1d9;
    --muted: #8b949e; --tag: #7ee787; --attr: #79c0ff;
    --val: #a5d6ff; --comment: #6e7681;
  }}
  * {{ box-sizing: border-box; margin:0; padding:0; }}
  body {{ font-family:'Segoe UI',system-ui,sans-serif; background:var(--bg); color:var(--text); display:flex; min-height:100vh; }}

  /* ── SIDEBAR ── */
  nav {{ position:fixed; top:0; left:0; width:220px; height:100vh; background:var(--surface);
         border-right:1px solid var(--border); padding:1.2rem .8rem; overflow-y:auto; z-index:10; }}
  nav h1 {{ font-size:.9rem; color:var(--blue); margin-bottom:1rem; padding-bottom:.5rem;
             border-bottom:1px solid var(--border); }}
  .nav-btn {{ display:block; width:100%; text-align:left; background:none; border:none; cursor:pointer;
               color:var(--muted); font-size:.78rem; padding:.4rem .6rem; border-radius:6px;
               margin-bottom:.2rem; transition:.15s; word-break:break-all; }}
  .nav-btn:hover, .nav-btn.active {{ background:#21262d; color:var(--text); }}
  .nav-btn.active {{ color:var(--blue); font-weight:600; }}

  /* ── MAIN ── */
  main {{ margin-left:220px; padding:2rem 2.5rem; flex:1; }}
  .page-title {{ font-size:1.4rem; color:#f0f6fc; margin-bottom:1.8rem; font-weight:700; }}

  /* ── PANEL ── */
  .panel {{ background:var(--surface); border:1px solid var(--border); border-radius:10px;
             margin-bottom:2rem; overflow:hidden; }}
  .panel-header {{ padding:.8rem 1.2rem; border-bottom:1px solid var(--border);
                   display:flex; align-items:center; gap:.8rem; }}
  .file-icon {{ font-size:1.1rem; }}
  .file-name {{ color:var(--blue); font-weight:600; font-size:.95rem; }}
  .toolbar {{ margin-left:auto; display:flex; gap:.5rem; }}
  .btn {{ background:#21262d; border:1px solid var(--border); color:var(--text); font-size:.75rem;
           padding:.3rem .7rem; border-radius:6px; cursor:pointer; transition:.15s; }}
  .btn:hover {{ background:#30363d; }}

  /* ── XML TREE ── */
  .xml-view {{ padding:1.2rem 1.5rem; overflow:auto; max-height:70vh; font-size:.78rem;
                font-family:'Cascadia Code','Fira Code',Consolas,monospace; line-height:1.7; }}
  .node {{ padding-left:1.4em; }}
  .toggler {{ cursor:pointer; user-select:none; color:var(--muted); margin-right:.3em;
               display:inline-block; width:.9em; text-align:center; }}
  .toggler:hover {{ color:var(--text); }}
  .tag  {{ color:var(--tag); }}
  .attr-name {{ color:var(--attr); }}
  .attr-val  {{ color:var(--val); }}
  .text-val  {{ color:var(--text); }}
  .comment   {{ color:var(--comment); font-style:italic; }}
  .pi        {{ color:var(--muted); }}
  .collapsed > .children {{ display:none; }}
</style>
</head>
<body>
<nav>
  <h1>📄 Resultados XQuery</h1>
  <div id="navLinks"></div>
</nav>
<main>
  <p class="page-title">Resultados XQuery — Yahoo Answers</p>
  <div id="panels"></div>
</main>

<script>
const FILES = [{js_data}];

// ── Build navigation ──
const navDiv = document.getElementById('navLinks');
FILES.forEach((f, i) => {{
  const btn = document.createElement('button');
  btn.className = 'nav-btn' + (i===0?' active':'');
  btn.textContent = f.name;
  btn.onclick = () => {{
    document.querySelectorAll('.nav-btn').forEach(b=>b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.panel')[i].scrollIntoView({{behavior:'smooth',block:'start'}});
  }};
  navDiv.appendChild(btn);
}});

// ── XML → HTML tree ──
function escT(s) {{
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}}
function renderNode(node) {{
  if (node.nodeType === 8) {{ // comment
    return `<div class="comment">&lt;!--${{escT(node.nodeValue)}}--&gt;</div>`;
  }}
  if (node.nodeType === 7) {{ // PI
    return `<div class="pi">&lt;?${{escT(node.nodeName)}} ${{escT(node.nodeValue)}}?&gt;</div>`;
  }}
  if (node.nodeType === 3) {{ // text
    const t = node.nodeValue.trim();
    return t ? `<span class="text-val">${{escT(t)}}</span>` : '';
  }}
  if (node.nodeType !== 1) return '';

  const name = escT(node.nodeName);
  let attrs = '';
  for (const a of node.attributes) {{
    attrs += ` <span class="attr-name">${{escT(a.name)}}</span>=<span class="attr-val">"${{escT(a.value)}}"</span>`;
  }}

  const kids = [...node.childNodes].filter(n =>
    n.nodeType === 1 || (n.nodeType === 3 && n.nodeValue.trim())
  );

  if (kids.length === 0) {{
    return `<div><span class="tag">&lt;${{name}}</span>${{attrs}}<span class="tag">/&gt;</span></div>`;
  }}

  const childrenHtml = kids.map(renderNode).join('');
  const id = 'n'+(Math.random()*1e9|0);

  if (kids.length === 1 && kids[0].nodeType === 3) {{
    // inline text
    return `<div><span class="tag">&lt;${{name}}</span>${{attrs}}<span class="tag">&gt;</span>`+
           `${{childrenHtml}}<span class="tag">&lt;/${{name}}&gt;</span></div>`;
  }}

  return `<div class="node-wrap" id="${{id}}">` +
    `<div><span class="toggler" onclick="toggle('${{id}}')" title="colapsar">▾</span>` +
    `<span class="tag">&lt;${{name}}</span>${{attrs}}<span class="tag">&gt;</span></div>` +
    `<div class="node children">${{childrenHtml}}</div>` +
    `<div><span class="tag">&lt;/${{name}}&gt;</span></div>` +
    `</div>`;
}}

function toggle(id) {{
  const el = document.getElementById(id);
  const tog = el.querySelector('.toggler');
  const collapsed = el.classList.toggle('collapsed');
  tog.textContent = collapsed ? '▸' : '▾';
}}

function expandAll(panelEl) {{
  panelEl.querySelectorAll('.node-wrap').forEach(n => {{
    n.classList.remove('collapsed');
    const t = n.querySelector(':scope > div > .toggler');
    if (t) t.textContent = '▾';
  }});
}}
function collapseAll(panelEl) {{
  panelEl.querySelectorAll('.node-wrap').forEach(n => {{
    n.classList.add('collapsed');
    const t = n.querySelector(':scope > div > .toggler');
    if (t) t.textContent = '▸';
  }});
}}

// ── Build panels ──
const panelsDiv = document.getElementById('panels');
FILES.forEach((f, i) => {{
  const parser = new DOMParser();
  const doc = parser.parseFromString(f.xml, 'text/xml');
  const root = doc.documentElement;

  // skip exist:result wrapper if present — go to first real child
  let target = root;
  if (root.localName === 'result' && root.namespaceURI && root.namespaceURI.includes('exist')) {{
    const first = [...root.childNodes].find(n=>n.nodeType===1);
    if (first) target = first;
  }}

  const treeHtml = renderNode(target);

  const panel = document.createElement('div');
  panel.className = 'panel';
  panel.innerHTML = `
    <div class="panel-header">
      <span class="file-icon">📄</span>
      <span class="file-name">${{f.name}}</span>
      <div class="toolbar">
        <button class="btn" onclick="expandAll(this.closest('.panel'))">Expandir todo</button>
        <button class="btn" onclick="collapseAll(this.closest('.panel'))">Colapsar todo</button>
      </div>
    </div>
    <div class="xml-view">${{treeHtml}}</div>`;
  panelsDiv.appendChild(panel);
}});
</script>
</body>
</html>"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", encoding="utf-8", delete=False) as f:
        f.write(html_content)
        tmp = f.name

    print(f"Visor abierto: {tmp}")
    webbrowser.open(f"file:///{tmp.replace(os.sep, '/')}")

if __name__ == "__main__":
    main()
