import requests
import argparse
from pathlib import Path

XQUERY_DIR = Path(__file__).parent.parent / "xquery"

parser = argparse.ArgumentParser()
parser.add_argument("consulta", nargs="?")
parser.add_argument("--todos",    action="store_true")
parser.add_argument("--output",   default=None)
parser.add_argument("--host",     default="localhost")
parser.add_argument("--port",     default="8080")
parser.add_argument("--user",     default="admin")
parser.add_argument("--password", default="admin")
args = parser.parse_args()

base = f"http://{args.host}:{args.port}/exist/rest"
auth = (args.user, args.password)

if args.todos:
    ficheros = sorted(XQUERY_DIR.glob("*.xq"))
elif args.consulta:
    ficheros = [Path(args.consulta)]
else:
    print("Indica un fichero .xq o usa --todos")
    exit(1)

if args.output:
    out_dir = Path(args.output)
    out_dir.mkdir(parents=True, exist_ok=True)

for xq in ficheros:
    print(f"Ejecutando {xq.name} ...", end=" ", flush=True)
    query = xq.read_text(encoding="utf-8")
    try:
        # POST con form-encoding: soporta queries de cualquier longitud
        # (GET tiene límite de URL ~8 KB que fallaría con las queries largas)
        r = requests.post(
            base + "/db",
            data={"_query": query, "_indent": "yes"},
            auth=auth,
            timeout=300,
            headers={"Accept": "application/xml"},
        )
    except requests.exceptions.ConnectionError:
        print("\n\nERROR: No se puede conectar a eXist-db en", base)
        print("  Asegúrate de que eXist-db está corriendo:")
        print("  Windows: %USERPROFILE%\\eXist-db\\bin\\startup.bat")
        exit(1)
    except requests.exceptions.ReadTimeout:
        print(f"\n  ERROR: La query tardó más de 300 s. Prueba a ejecutarla sola:")
        print(f"  python existdb/ejecutar_xquery.py {xq}")
        continue

    if r.status_code != 200:
        print(f"Error HTTP {r.status_code}")
        print(r.text[:500])
        continue

    print("OK")
    print(r.text[:3000])

    if args.output:
        dest = out_dir / (xq.stem + "_resultado.xml")
        # Inyectar PI xml-stylesheet para que el navegador aplique el XSLT
        xml_text = r.text
        pi = '<?xml-stylesheet type="text/xsl" href="resultado.xsl"?>\n'
        if "?>" in xml_text[:80]:                    # hay declaración <?xml ...?>
            end_decl = xml_text.index("?>") + 2
            xml_text = xml_text[:end_decl] + "\n" + pi + xml_text[end_decl:]
        else:
            xml_text = pi + xml_text
        dest.write_text(xml_text, encoding="utf-8")
        print(f"  → Guardado en {dest}")
