import xml.sax
import xml.sax.handler
from pathlib import Path

DATA_DIR    = Path(__file__).parent.parent / "data"
XML_FILE    = DATA_DIR / "FullOct2007.xml"
OUTPUT_FILE = DATA_DIR / "categorias.txt"


class CategoryHandler(xml.sax.handler.ContentHandler):
    def __init__(self):
        self.current_tag = None
        self.current_text = []
        self.maincat = ""
        self.subcat = ""
        self.cat = ""
        self.tags_of_interest = {"maincat", "subcat", "cat"}
        self.categories = set()
        self.count = 0

    def startElement(self, name, attrs):
        if name in self.tags_of_interest:
            self.current_tag = name
            self.current_text = []

    def characters(self, content):
        if self.current_tag:
            self.current_text.append(content)

    def endElement(self, name):
        if name in self.tags_of_interest and self.current_tag == name:
            text = "".join(self.current_text).strip()
            if name == "maincat":
                self.maincat = text
            elif name == "subcat":
                self.subcat = text
            elif name == "cat":
                self.cat = text
            self.current_tag = None

        elif name == "document":
            self.categories.add((self.maincat, self.subcat, self.cat))
            self.count += 1
            if self.count % 100_000 == 0:
                print("Procesados", self.count, "documentos")
            self.maincat = self.subcat = self.cat = ""


if not XML_FILE.exists():
    print("No se encontro el fichero", XML_FILE)
    exit(1)

print("Procesando", XML_FILE.name)

handler = CategoryHandler()
parser = xml.sax.make_parser()
parser.setContentHandler(handler)
parser.setFeature(xml.sax.handler.feature_validation, False)
parser.setFeature(xml.sax.handler.feature_namespaces, False)

class WrappedFile:
    def __init__(self, fh):
        self._fh = fh
        self._state = "header"

    def read(self, size=65536):
        if self._state == "header":
            self._state = "body"
            return b"<root>"
        elif self._state == "body":
            data = self._fh.read(size)
            if not data:
                self._state = "footer"
                return b"</root>"
            return data
        return b""

try:
    with open(XML_FILE, "rb") as f:
        parser.parse(WrappedFile(f))
except Exception as e:
    print("El parser termino con un error:", e)

sorted_cats = sorted(handler.categories)

with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    out.write(f"TOTAL documentos procesados: {handler.count:,}\n")
    out.write(f"Combinaciones unicas de categoria: {len(sorted_cats)}\n")
    out.write(f"{'='*70}\n\n")
    out.write(f"{'MAINCAT':<35} {'SUBCAT':<35} {'CAT'}\n")
    out.write(f"{'-'*70}\n")
    for maincat, subcat, cat in sorted_cats:
        out.write(f"{maincat:<35} {subcat:<35} {cat}\n")

print("Total documentos:", handler.count)
print("Categorias unicas:", len(sorted_cats))
print("Resultado guardado en", OUTPUT_FILE)
