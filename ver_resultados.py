import os
import glob
import webbrowser
import tempfile
from xml.etree import ElementTree as ET

RESULTADOS_DIR = os.path.join(os.path.dirname(__file__), "resultados")
NS = "http://exist.sourceforge.net/NS/exist"


def load(path):
    root = ET.parse(path).getroot()
    if root.tag == f"{{{NS}}}result":
        for child in root:
            if not child.tag.startswith(f"{{{NS}}}"):
                return child
    return root


def parse_estadisticas(root):
    cats = []
    totales = {}
    for idioma in root.findall("idioma"):
        lang = idioma.get("codigo")
        for cat in idioma.findall("categoria"):
            cats.append({
                "nombre":      cat.get("nombre"),
                "lang":        lang,
                "preguntas":   int(cat.findtext("total_preguntas") or 0),
                "respuestas":  int(cat.findtext("total_respuestas") or 0),
                "media":       float(cat.findtext("media_respuestas") or 0),
                "sin_content": int(cat.findtext("sin_content") or 0),
                "subcats": [
                    {"nombre": s.get("nombre"), "total": int(s.get("total", 0))}
                    for s in cat.findall("subcategorias/subcat")
                ]
            })
        tot = idioma.find("totales")
        if tot is not None:
            totales[lang] = {
                "preguntas": int(tot.findtext("preguntas") or 0),
                "respuestas": int(tot.findtext("respuestas") or 0),
                "uq_preg": int(tot.findtext("usuarios_unicos_preguntando") or 0),
                "uq_resp": int(tot.findtext("usuarios_unicos_respondiendo") or 0),
            }
    return {"categorias": cats, "totales": totales}


def parse_redes(root):
    sim = root.find("simetria")
    return {
        "simetria": {
            "total":     int(sim.findtext("total_usuarios_distintos") or 0),
            "solo_preg": int(sim.find("solo_preguntan").get("total", 0)),
            "solo_resp": int(sim.find("solo_responden").get("total", 0)),
            "ambas":     int(sim.find("preguntan_y_responden").get("total", 0)),
        },
        "top_respondedores": [
            {"id": u.get("id"), "n": int(u.get("mejores_respuestas", 0))}
            for u in root.findall("top_respondedores/usuario")
        ],
        "top_preguntadores": [
            {"id": u.get("id"), "n": int(u.get("preguntas", 0))}
            for u in root.findall("top_preguntadores/usuario")
        ],
        "simetria_cats": [
            {
                "nombre": c.get("nombre"),
                "preg":   int(c.get("preguntadores", 0)),
                "resp":   int(c.get("respondedores", 0)),
                "ambas":  int(c.get("ambas_cosas", 0)),
            }
            for c in root.findall("simetria_por_categoria/categoria")
        ],
        "puentes": int(0 if root.find("puentes_es_it/resumen") is None else int(root.find("puentes_es_it/resumen").get("total_puentes", 0)))
                   if root.find("puentes_es_it/resumen") is not None else 0,
    }


def parse_calidad(root):
    return {
        "completitud": [
            {
                "campo":     c.get("nombre"),
                "presentes": int(c.get("presentes", 0)),
                "ausentes":  int(c.get("ausentes", 0)),
            }
            for c in root.findall("completitud/campo")
        ],
        "anomalias": {
            "bestanswer_corto": int((root.find("anomalias/bestanswer_muy_corto/resultado") or ET.Element("x")).get("total", 0)),
            "una_respuesta":    int((root.find("anomalias/una_sola_respuesta/resultado")   or ET.Element("x")).get("total", 0)),
            "subject_corto":    int((root.find("anomalias/subject_muy_corto/resultado")    or ET.Element("x")).get("total", 0)),
        },
        "velocidad": {
            "mismo_dia": int((root.find("velocidad_resolucion/mismo_dia") or ET.Element("x")).get("total", 0)),
            "pct":       (root.find("velocidad_resolucion/mismo_dia") or ET.Element("x")).get("porcentaje", "0%"),
        },
        "por_cat": [
            {
                "nombre":     c.get("nombre"),
                "sin_content": int(c.get("sin_content", 0)),
                "total":      int(c.get("total", 0)),
                "media_best": float(c.get("bestanswer_media_chars", 0)),
                "media_resp": float(c.get("media_respuestas", 0)),
            }
            for c in root.findall("resumen_por_categoria/categoria")
        ],
    }


# Términos que pertenecen al español vs italiano
_TERMS_IT = {"immigrazione", "immigrante", "legge", "governo"}


def parse_avanzadas(root):
    comparativa = [
        {"metrica": i.get("metrica"), "ES": i.get("ES"), "IT": i.get("IT")}
        for i in root.findall("comparativa_es_it/item")
    ]
    all_temas = sorted(
        [{"texto": t.get("texto"), "n": int(t.get("menciones", 0))}
         for t in root.findall("temas_politica/termino")],
        key=lambda x: x["n"], reverse=True
    )
    temas_es = [t for t in all_temas if t["texto"] not in _TERMS_IT]
    temas_it = [t for t in all_temas if t["texto"] in _TERMS_IT]
    return {
        "comparativa": comparativa,
        "temas_es": temas_es,
        "temas_it": temas_it,
        "sin_respuestas": int((root.find("sin_respuestas/resultado") or ET.Element("x")).get("total", 0)),
    }


def js_list(values):
    return "[" + ",".join(str(v) for v in values) + "]"


def js_labels(strings):
    escaped = [s.replace("'", "\\'") for s in strings]
    return "[" + ",".join(f"'{s}'" for s in escaped) + "]"


def build_html(est, red, cal, avz):
    cats = est["categorias"]
    tot  = est["totales"]
    total_preg = sum(c["preguntas"] for c in cats)
    total_resp = sum(c["respuestas"] for c in cats)
    uq_preg = sum(t.get("uq_preg", 0) for t in tot.values())
    uq_resp = sum(t.get("uq_resp", 0) for t in tot.values())

    # Solo categorías de Política y Gobierno para los gráficos de estadísticas
    cats_pol = [c for c in cats if "gobierno" in c["nombre"].lower() or "governo" in c["nombre"].lower()]

    cat_es_pol = next((c for c in cats if "Gobierno" in c["nombre"] and c["lang"] == "es"), {"subcats": []})
    cat_it_pol = next((c for c in cats if "governo" in c["nombre"]), {"subcats": []})

    subcat_es_labels = js_labels([s["nombre"] for s in cat_es_pol["subcats"][:10]])
    subcat_es_data   = js_list([s["total"] for s in cat_es_pol["subcats"][:10]])
    subcat_it_labels = js_labels([s["nombre"] for s in cat_it_pol["subcats"][:10]])
    subcat_it_data   = js_list([s["total"] for s in cat_it_pol["subcats"][:10]])

    comp_rows = "".join(
        f"<tr><td>{r['metrica']}</td><td>{r['ES']}</td><td>{r['IT']}</td></tr>"
        for r in avz["comparativa"]
    )
    top_preg_rows = "".join(
        f"<tr><td>{u['id']}</td><td>{u['n']}</td></tr>"
        for u in red["top_preguntadores"]
    )

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<title>Yahoo Answers — Analisis</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@500&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0e0f14;
  --surface:#16181f;
  --surface2:#1e2029;
  --border:#2a2d3a;
  --accent:#c8f04a;
  --accent2:#7b6af5;
  --es:#4ab8f0;
  --it:#f06b4a;
  --text:#e8eaf0;
  --muted:#6b7080;
  --green:#4af0a0;
  --yellow:#f0c44a;
}}
body{{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}}

header{{
  padding:28px 40px 24px;
  border-bottom:1px solid var(--border);
  display:flex;align-items:flex-end;justify-content:space-between;
  background:var(--surface);
}}
header .title{{
  font-size:1.25rem;font-weight:700;letter-spacing:-0.02em;
  color:var(--text);
}}
header .title span{{color:var(--accent)}}
header .sub{{
  font-size:0.78rem;color:var(--muted);margin-top:5px;
  font-family:'JetBrains Mono',monospace;
}}
header .chips{{display:flex;gap:8px}}
.chip{{
  font-size:0.72rem;font-weight:600;padding:4px 10px;border-radius:20px;
  font-family:'JetBrains Mono',monospace;letter-spacing:0.03em;
}}
.chip-es{{background:rgba(74,184,240,0.15);color:var(--es);border:1px solid rgba(74,184,240,0.3)}}
.chip-it{{background:rgba(240,107,74,0.15);color:var(--it);border:1px solid rgba(240,107,74,0.3)}}

nav{{
  background:var(--surface);
  border-bottom:1px solid var(--border);
  padding:0 40px;
  display:flex;gap:2px;
  position:sticky;top:0;z-index:100;
}}
nav a{{
  display:inline-block;padding:14px 18px;
  font-size:0.82rem;font-weight:500;color:var(--muted);
  text-decoration:none;cursor:pointer;
  border-bottom:2px solid transparent;
  transition:color .15s,border-color .15s;
  letter-spacing:0.01em;
}}
nav a:hover{{color:var(--text)}}
nav a.active{{color:var(--accent);border-bottom-color:var(--accent)}}

.content{{max-width:1120px;margin:0 auto;padding:32px 40px}}
.section{{display:none}}
.section.active{{display:block}}

h2{{
  font-size:0.72rem;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;
  color:var(--muted);margin-bottom:24px;padding-bottom:12px;
  border-bottom:1px solid var(--border);
}}
h3{{font-size:0.85rem;font-weight:600;color:var(--text);margin-bottom:14px;letter-spacing:-0.01em}}

.grid{{display:grid;gap:16px;margin-bottom:20px}}
.g2{{grid-template-columns:repeat(2,1fr)}}
.g4{{grid-template-columns:repeat(4,1fr)}}

.card{{
  background:var(--surface);border:1px solid var(--border);
  border-radius:10px;padding:20px;
}}
.stat{{text-align:center;padding:24px 16px}}
.stat .num{{
  font-size:2.2rem;font-weight:700;font-family:'JetBrains Mono',monospace;
  color:var(--accent);letter-spacing:-0.03em;
}}
.stat .lbl{{font-size:0.75rem;color:var(--muted);margin-top:6px;line-height:1.4}}

.chart-card{{
  background:var(--surface);border:1px solid var(--border);
  border-radius:10px;padding:20px 22px;margin-bottom:20px;
}}
.ch{{position:relative;height:260px}}
.ch-sm{{position:relative;height:210px}}

table{{width:100%;border-collapse:collapse;font-size:0.82rem}}
th{{
  padding:9px 14px;text-align:left;
  color:var(--muted);font-weight:500;font-size:0.75rem;
  text-transform:uppercase;letter-spacing:0.07em;
  border-bottom:1px solid var(--border);
}}
td{{padding:9px 14px;border-bottom:1px solid var(--border);color:var(--text)}}
tr:last-child td{{border-bottom:none}}
tr:hover td{{background:var(--surface2)}}
td:last-child{{font-family:'JetBrains Mono',monospace;font-size:0.8rem;color:var(--accent)}}

.badge{{
  display:inline-block;padding:3px 9px;border-radius:4px;
  font-size:0.72rem;font-weight:600;font-family:'JetBrains Mono',monospace;
  letter-spacing:0.05em;
}}
.es{{background:rgba(74,184,240,0.15);color:var(--es)}}
.it{{background:rgba(240,107,74,0.15);color:var(--it)}}

.info-box{{
  background:var(--surface2);border:1px solid var(--border);
  border-radius:10px;padding:24px;
  display:flex;flex-direction:column;justify-content:center;align-items:center;
  text-align:center;gap:10px;
}}
.info-box .big{{
  font-size:2.6rem;font-weight:700;font-family:'JetBrains Mono',monospace;
  letter-spacing:-0.04em;
}}
.info-box .desc{{font-size:0.82rem;color:var(--muted);line-height:1.5;max-width:240px}}

@media(max-width:700px){{.g2,.g4{{grid-template-columns:1fr}}}}
</style>
</head>
<body>

<header>
  <div>
    <div class="title">Yahoo <span>Answers</span> — Análisis de preguntas</div>
  </div>
  <div class="chips">
    <span class="chip chip-es">ES · Política · Actualidad</span>
    <span class="chip chip-it">IT · Politica · Eventi</span>
  </div>
</header>

<nav>
  <a class="active" onclick="show('s1',this)">Estadísticas</a>
  <a onclick="show('s2',this)">Redes Sociales</a>
  <a onclick="show('s3',this)">Calidad de Datos</a>
  <a onclick="show('s4',this)">Consultas Avanzadas</a>
</nav>

<div class="content">

<div id="s1" class="section active">
  <h2>Estadísticas Generales</h2>
  <div class="grid g4">
    <div class="card stat"><div class="num">{total_preg:,}</div><div class="lbl">Preguntas totales</div></div>
    <div class="card stat"><div class="num" style="color:var(--accent2)">{total_resp:,}</div><div class="lbl">Respuestas totales</div></div>
    <div class="card stat"><div class="num" style="color:var(--es)">{uq_preg:,}</div><div class="lbl">Usuarios distintos preguntando</div></div>
    <div class="card stat"><div class="num" style="color:var(--green)">{uq_resp:,}</div><div class="lbl">Usuarios distintos respondiendo</div></div>
  </div>
  <div class="grid g2">
    <div class="chart-card"><h3>Preguntas — Política y Gobierno (ES vs IT)</h3><div class="ch"><canvas id="cPreg"></canvas></div></div>
    <div class="chart-card"><h3>Media de respuestas por pregunta (ES vs IT)</h3><div class="ch"><canvas id="cMedia"></canvas></div></div>
  </div>
  <div class="chart-card"><h3>Subcategorias — Política y Gobierno (ES)</h3><div class="ch"><canvas id="cSubES"></canvas></div></div>
  <div class="chart-card"><h3>Subcategorias — Politica e governo (IT)</h3><div class="ch-sm"><canvas id="cSubIT"></canvas></div></div>
</div>

<div id="s2" class="section">
  <h2>Analisis de Redes Sociales</h2>
  <div class="grid g4">
    <div class="card stat"><div class="num">{red['simetria']['total']:,}</div><div class="lbl">Usuarios totales distintos</div></div>
    <div class="card stat"><div class="num" style="color:var(--yellow)">{red['simetria']['solo_preg']:,}</div><div class="lbl">Solo preguntan</div></div>
    <div class="card stat"><div class="num" style="color:var(--it)">{red['simetria']['solo_resp']:,}</div><div class="lbl">Solo responden</div></div>
    <div class="card stat"><div class="num" style="color:var(--green)">{red['simetria']['ambas']:,}</div><div class="lbl">Hacen ambas cosas</div></div>
  </div>
  <div class="grid g2">
    <div class="chart-card"><h3>Simetria global</h3><div class="ch"><canvas id="cSim"></canvas></div></div>
    <div class="chart-card"><h3>Top 10 respondedores</h3><div class="ch"><canvas id="cTopR"></canvas></div></div>
  </div>
  <div class="chart-card"><h3>Simetria por categoria</h3><div class="ch"><canvas id="cSimCat"></canvas></div></div>
  <div class="grid g2" style="margin-top:0">
    <div class="card"><h3 style="margin-bottom:14px">Top 10 preguntadores</h3>
      <table><tr><th>Usuario</th><th>Preguntas</th></tr>{top_preg_rows}</table>
    </div>
    <div class="info-box">
      <div class="big" style="color:var(--accent2)">{red['puentes']}</div>
      <div class="desc">Usuarios activos en ambas comunidades ES e IT. Las dos comunidades son practicamente independientes entre si.</div>
    </div>
  </div>
</div>

<div id="s3" class="section">
  <h2>Calidad de Datos</h2>
  <div class="grid g2">
    <div class="chart-card"><h3>Completitud de campos opcionales</h3><div class="ch"><canvas id="cComp"></canvas></div></div>
    <div class="chart-card"><h3>Anomalias detectadas</h3><div class="ch"><canvas id="cAnom"></canvas></div></div>
  </div>
  <div class="chart-card"><h3>Longitud media del bestanswer por categoria (caracteres)</h3><div class="ch-sm"><canvas id="cLong"></canvas></div></div>
  <div class="grid g2" style="margin-top:0">
    <div class="chart-card" style="margin-bottom:0"><h3>Media de respuestas por categoria</h3><div class="ch-sm"><canvas id="cMedR"></canvas></div></div>
    <div class="card" style="display:flex;flex-direction:column;gap:20px;justify-content:center">
      <div class="stat" style="padding:0"><div class="num" style="color:var(--yellow)">{cal['velocidad']['mismo_dia']:,}</div><div class="lbl">Resueltas el mismo dia ({cal['velocidad']['pct']})</div></div>
      <div class="stat" style="padding:0"><div class="num" style="color:var(--it)">{cal['anomalias']['bestanswer_corto']:,}</div><div class="lbl">Mejores respuestas muy cortas (menos de 20 chars)</div></div>
      <div class="stat" style="padding:0"><div class="num" style="color:var(--accent2)">{cal['anomalias']['una_respuesta']:,}</div><div class="lbl">Preguntas con una sola respuesta</div></div>
    </div>
  </div>
</div>

<div id="s4" class="section">
  <h2>Consultas Avanzadas</h2>
  <div class="chart-card">
    <h3>Comparativa ES vs IT</h3>
    <table>
      <tr><th>Metrica</th><th><span class="badge es">ES</span></th><th><span class="badge it">IT</span></th></tr>
      {comp_rows}
    </table>
  </div>
  <div class="grid g2" style="margin-top:0">
    <div class="chart-card" style="margin-bottom:0"><h3>Palabras clave — Política ES <span class="badge es">ES</span></h3><div class="ch"><canvas id="cTemasES"></canvas></div></div>
    <div class="chart-card" style="margin-bottom:0"><h3>Parole chiave — Politica IT <span class="badge it">IT</span></h3><div class="ch"><canvas id="cTemasIT"></canvas></div></div>
  </div>
  <div class="chart-card" style="margin-top:16px">
    <h3>Longitud media de respuestas y preguntas — ES vs IT</h3>
    <div class="ch"><canvas id="cLongComp"></canvas></div>
  </div>
  <div class="info-box" style="margin-top:16px">
    <div class="big" style="color:var(--green)">{avz['sin_respuestas']}</div>
    <div class="desc">Preguntas sin ninguna respuesta. Todas las preguntas del corpus tienen al menos una respuesta registrada.</div>
  </div>
</div>

</div>
<script>
function show(id, el) {{
  document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
  document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  el.classList.add('active');
}}

Chart.defaults.color = '#6b7080';
Chart.defaults.font.family = 'Inter, sans-serif';
Chart.defaults.font.size = 11;

const G  = {{color:'rgba(255,255,255,0.05)'}};
const C4 = ['#4ab8f0','#f06b4a','#4af0a0','#c8f04a'];
const C4a = ['rgba(74,184,240,0.75)','rgba(240,107,74,0.75)','rgba(74,240,160,0.75)','rgba(200,240,74,0.75)'];

function barV(id, labels, data, colors, yLabel) {{
  new Chart(document.getElementById(id), {{
    type:'bar',
    data:{{labels, datasets:[{{data,
      backgroundColor:Array.isArray(colors)?colors:labels.map(()=>colors),
      borderRadius:5, borderSkipped:false}}]}},
    options:{{responsive:true,maintainAspectRatio:false,
      plugins:{{legend:{{display:false}}}},
      scales:{{
        y:{{grid:G,border:{{display:false}},ticks:{{color:'#6b7080'}},
           title:{{display:!!yLabel,text:yLabel,color:'#6b7080'}}}},
        x:{{grid:{{display:false}},border:{{display:false}},ticks:{{color:'#6b7080'}}}}
      }}
    }}
  }});
}}
function barH(id, labels, data, colors) {{
  new Chart(document.getElementById(id), {{
    type:'bar',
    data:{{labels, datasets:[{{data,
      backgroundColor:Array.isArray(colors)?colors:labels.map(()=>colors),
      borderRadius:5, borderSkipped:false}}]}},
    options:{{indexAxis:'y',responsive:true,maintainAspectRatio:false,
      plugins:{{legend:{{display:false}}}},
      scales:{{
        x:{{grid:G,border:{{display:false}},ticks:{{color:'#6b7080'}}}},
        y:{{grid:{{display:false}},border:{{display:false}},ticks:{{color:'#6b7080'}}}}
      }}
    }}
  }});
}}

// Gráficos sección 1 — solo Política y Gobierno
new Chart(document.getElementById('cPreg'), {{
  type:'bar',
  data:{{
    labels:['Política y Gobierno (ES)','Politica e governo (IT)'],
    datasets:[{{
      data:[{cat_es_pol.get('preguntas', 0)},{cat_it_pol.get('preguntas', 0)}],
      backgroundColor:['rgba(74,184,240,0.75)','rgba(240,107,74,0.75)'],
      borderRadius:5,borderSkipped:false
    }}]
  }},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}}}},
    scales:{{y:{{grid:G,border:{{display:false}},ticks:{{color:'#6b7080'}}}},x:{{grid:{{display:false}},border:{{display:false}},ticks:{{color:'#6b7080'}}}}}}
  }}
}});
new Chart(document.getElementById('cMedia'), {{
  type:'bar',
  data:{{
    labels:['Política y Gobierno (ES)','Politica e governo (IT)'],
    datasets:[{{
      data:[{cat_es_pol.get('media', 0)},{cat_it_pol.get('media', 0)}],
      backgroundColor:['rgba(74,184,240,0.75)','rgba(240,107,74,0.75)'],
      borderRadius:5,borderSkipped:false
    }}]
  }},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{display:false}}}},
    scales:{{y:{{grid:G,border:{{display:false}},ticks:{{color:'#6b7080'}},title:{{display:true,text:'Media respuestas',color:'#6b7080'}}}},x:{{grid:{{display:false}},border:{{display:false}},ticks:{{color:'#6b7080'}}}}}}
  }}
}});
barH('cSubES', {subcat_es_labels}, {subcat_es_data}, 'rgba(74,184,240,0.75)');
barH('cSubIT', {subcat_it_labels}, {subcat_it_data}, 'rgba(240,107,74,0.75)');

new Chart(document.getElementById('cSim'), {{
  type:'doughnut',
  data:{{
    labels:['Solo preguntan','Solo responden','Ambas cosas'],
    datasets:[{{
      data:[{red['simetria']['solo_preg']},{red['simetria']['solo_resp']},{red['simetria']['ambas']}],
      backgroundColor:['rgba(200,240,74,0.8)','rgba(240,107,74,0.8)','rgba(74,240,160,0.8)'],
      borderWidth:3,borderColor:'#16181f'
    }}]
  }},
  options:{{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'right',labels:{{color:'#6b7080',boxWidth:12,padding:16}}}}}}
  }}
}});

barH('cTopR',
  {js_labels([u['id'] for u in red['top_respondedores']])},
  {js_list([u['n'] for u in red['top_respondedores']])},
  'rgba(123,106,245,0.8)');

new Chart(document.getElementById('cSimCat'), {{
  type:'bar',
  data:{{
    labels:{js_labels([c['nombre'] for c in red['simetria_cats']])},
    datasets:[
      {{label:'Solo preguntan', data:{js_list([c['preg']-c['ambas'] for c in red['simetria_cats']])}, backgroundColor:'rgba(200,240,74,0.75)',borderRadius:4}},
      {{label:'Solo responden', data:{js_list([c['resp']-c['ambas'] for c in red['simetria_cats']])}, backgroundColor:'rgba(240,107,74,0.75)',borderRadius:4}},
      {{label:'Ambas cosas',    data:{js_list([c['ambas'] for c in red['simetria_cats']])},            backgroundColor:'rgba(74,240,160,0.75)',borderRadius:4}},
    ]
  }},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{
      x:{{stacked:true,grid:{{display:false}},border:{{display:false}},ticks:{{color:'#6b7080'}}}},
      y:{{stacked:true,grid:G,border:{{display:false}},ticks:{{color:'#6b7080'}}}}
    }},
    plugins:{{legend:{{position:'top',labels:{{color:'#6b7080',boxWidth:12,padding:16}}}}}}
  }}
}});

new Chart(document.getElementById('cComp'), {{
  type:'bar',
  data:{{
    labels:{js_labels([c['campo'] for c in cal['completitud']])},
    datasets:[
      {{label:'Presentes',data:{js_list([c['presentes'] for c in cal['completitud']])},backgroundColor:'rgba(74,240,160,0.75)',borderRadius:4}},
      {{label:'Ausentes', data:{js_list([c['ausentes']  for c in cal['completitud']])},backgroundColor:'rgba(240,107,74,0.75)',borderRadius:4}},
    ]
  }},
  options:{{responsive:true,maintainAspectRatio:false,
    scales:{{
      x:{{stacked:true,grid:{{display:false}},border:{{display:false}},ticks:{{color:'#6b7080'}}}},
      y:{{stacked:true,grid:G,border:{{display:false}},ticks:{{color:'#6b7080'}}}}
    }},
    plugins:{{legend:{{position:'top',labels:{{color:'#6b7080',boxWidth:12,padding:16}}}}}}
  }}
}});

barV('cAnom',
  ['Bestanswer corto','Una sola respuesta','Subject corto'],
  [{cal['anomalias']['bestanswer_corto']},{cal['anomalias']['una_respuesta']},{cal['anomalias']['subject_corto']}],
  ['rgba(240,107,74,0.8)','rgba(200,240,74,0.8)','rgba(123,106,245,0.8)']);

barH('cLong',
  {js_labels([c['nombre'] for c in cal['por_cat']])},
  {js_list([c['media_best'] for c in cal['por_cat']])},
  C4a);

barV('cMedR',
  {js_labels([c['nombre'] for c in cal['por_cat']])},
  {js_list([c['media_resp'] for c in cal['por_cat']])},
  C4a, 'Media respuestas');

// Palabras clave separadas por idioma
barH('cTemasES',
  {js_labels([t['texto'] for t in avz['temas_es']])},
  {js_list([t['n'] for t in avz['temas_es']])},
  'rgba(74,184,240,0.8)');
barH('cTemasIT',
  {js_labels([t['texto'] for t in avz['temas_it']])},
  {js_list([t['n'] for t in avz['temas_it']])},
  'rgba(240,107,74,0.8)');

new Chart(document.getElementById('cLongComp'), {{
  type: 'bar',
  data: {{
    labels: {js_labels([r['metrica'] for r in avz['comparativa'] if r['metrica'] in ('Media longitud bestanswer', 'Media respuestas/pregunta')])},
    datasets: [
      {{
        label: 'ES',
        data: {js_list([float(r['ES'].replace('%','')) for r in avz['comparativa'] if r['metrica'] in ('Media longitud bestanswer', 'Media respuestas/pregunta')])},
        backgroundColor: 'rgba(74,184,240,0.75)', borderRadius: 5, borderSkipped: false
      }},
      {{
        label: 'IT',
        data: {js_list([float(r['IT'].replace('%','')) for r in avz['comparativa'] if r['metrica'] in ('Media longitud bestanswer', 'Media respuestas/pregunta')])},
        backgroundColor: 'rgba(240,107,74,0.75)', borderRadius: 5, borderSkipped: false
      }}
    ]
  }},
  options: {{responsive:true,maintainAspectRatio:false,
    plugins:{{legend:{{position:'top',labels:{{color:'#6b7080',boxWidth:12,padding:16}}}}}},
    scales:{{
      x:{{grid:{{display:false}},border:{{display:false}},ticks:{{color:'#6b7080'}}}},
      y:{{grid:G,border:{{display:false}},ticks:{{color:'#6b7080'}}}}
    }}
  }}
}});
</script>
</body>
</html>"""


files = {
    os.path.basename(p): p
    for p in glob.glob(os.path.join(RESULTADOS_DIR, "*.xml"))
}

if not files:
    print("No se encontraron ficheros XML en", RESULTADOS_DIR)
    exit(1)

est_path = next((v for k, v in files.items() if "estadistica" in k), None)
red_path = next((v for k, v in files.items() if "redes" in k), None)
cal_path = next((v for k, v in files.items() if "calidad" in k), None)
avz_path = next((v for k, v in files.items() if "avanzada" in k), None)

if not all([est_path, red_path, cal_path]):
    print("Faltan ficheros de resultados.")
    print("Encontrados:", list(files.keys()))
    exit(1)

est = parse_estadisticas(load(est_path))
red = parse_redes(load(red_path))
cal = parse_calidad(load(cal_path))
avz = parse_avanzadas(load(avz_path)) if avz_path else {"comparativa": [], "temas": [], "sin_respuestas": 0}

html_content = build_html(est, red, cal, avz)

with tempfile.NamedTemporaryFile(mode="w", suffix=".html", encoding="utf-8", delete=False) as f:
    f.write(html_content)
    tmp = f.name

print("Dashboard generado en", tmp)
webbrowser.open("file:///" + tmp.replace(os.sep, "/"))
