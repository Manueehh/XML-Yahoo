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
            combo = (self.maincat, self.subcat, self.cat)
            if combo not in self.categories:
                self.categories.add(combo)
            self.count += 1
            if self.count % 100_000 == 0:
                print(f"  Procesados: {self.count:,} documentos | "
                      f"Categorías únicas hasta ahora: {len(self.categories)}")
            self.maincat = self.subcat = self.cat = ""


def main():
    if not XML_FILE.exists():
        print(f"No se encontró el fichero: {XML_FILE}")
        return

    print(f"Procesando {XML_FILE.name} ({XML_FILE.stat().st_size / 1e9:.1f} GB)...")
    print("Esto puede tardar varios minutos...\n")

    handler = CategoryHandler()

    parser = xml.sax.make_parser()
    parser.setContentHandler(handler)
    parser.setFeature(xml.sax.handler.feature_validation, False)
    parser.setFeature(xml.sax.handler.feature_namespaces, False)

    try:
        with open(XML_FILE, "rb") as f:
            class WrappedFile:
                def __init__(self, fh):
                    self._fh = fh
                    self._header = b"<root>"
                    self._footer = b"</root>"
                    self._state = "header"

                def read(self, size=-1):
                    if self._state == "header":
                        self._state = "body"
                        return self._header
                    elif self._state == "body":
                        data = self._fh.read(size if size > 0 else 65536)
                        if not data:
                            self._state = "footer"
                            return self._footer
                        return data
                    else:
                        return b""

            parser.parse(WrappedFile(f))
    except Exception as e:
        print(f"\nEl parser encontró un error: {e}")
        print("Usando los datos recopilados hasta ese punto...\n")

    sorted_cats = sorted(handler.categories)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
        out.write(f"TOTAL documentos procesados: {handler.count:,}\n")
        out.write(f"Combinaciones únicas de categoría: {len(sorted_cats)}\n")
        out.write(f"{'MAINCAT':<35} {'SUBCAT':<35} {'CAT'}\n")
        for maincat, subcat, cat in sorted_cats:
            out.write(f"{maincat:<35} {subcat:<35} {cat}\n")

    print(f"\n{handler.count:,} documentos procesados.")
    print(f"{len(sorted_cats)} combinaciones de categoría únicas encontradas.")
    print(f"Resultado guardado en: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
