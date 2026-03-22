import requests
import argparse
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

FICHEROS = [
    ("preguntas_noticias_y_actualidad.xml",   "/db/yahooanswers/es"),
    ("preguntas_politica_y_gobierno.xml", "/db/yahooanswers/es"),
    ("preguntas_notizie_ed_eventi.xml",        "/db/yahooanswers/it"),
    ("preguntas_politica_e_governo.xml",       "/db/yahooanswers/it"),
]

parser = argparse.ArgumentParser()
parser.add_argument("--host",     default="localhost")
parser.add_argument("--port",     default="8080")
parser.add_argument("--user",     default="admin")
parser.add_argument("--password", default="admin")
args = parser.parse_args()

base = f"http://{args.host}:{args.port}/exist/rest"
auth = (args.user, args.password)

print("Conectando a eXist-db en", base)

for col in ["/db/yahooanswers", "/db/yahooanswers/es", "/db/yahooanswers/it"]:
    r = requests.request("MKCOL", base + col + "/", auth=auth, timeout=30)
    print("Coleccion", col, "- HTTP", r.status_code)

for nombre, coleccion in FICHEROS:
    ruta = DATA_DIR / nombre
    if not ruta.exists():
        print("No encontrado:", nombre)
        continue
    print("Subiendo", nombre)
    with open(ruta, "rb") as f:
        r = requests.put(
            base + coleccion + "/" + nombre,
            data=f,
            auth=auth,
            headers={"Content-Type": "application/xml"},
            timeout=300,
        )
    print("Resultado HTTP", r.status_code)

print("Carga terminada")
print("Panel eXist-db en http://" + args.host + ":" + args.port + "/exist/")
