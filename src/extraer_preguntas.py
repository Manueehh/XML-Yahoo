import xml.sax
import xml.sax.handler
import re
from pathlib import Path

TARGETS = {
    "Política y Gobierno",    # español
    "Noticias y Actualidad",  # español
    "Politica e governo",     # italiano
    "Notizie ed eventi",      # italiano
}

DATA_DIR = Path(__file__).parent.parent / "data"
XML_FILE = DATA_DIR / "FullOct2007.xml"


def slug(name: str) -> str:
    s = name.lower()
    s = s.replace(" ", "_")
    s = re.sub(r"[^\w]", "", s, flags=re.UNICODE)
    return s


def output_path(categoria: str) -> Path:
    return DATA_DIR / f"preguntas_{slug(categoria)}.xml"


class DocExtractor(xml.sax.handler.ContentHandler):

    def __init__(self, out_map: dict):
        self.out_map   = out_map
        self.in_doc    = False
        self.buf       = []
        self.maincat   = ""
        self.cur_tag   = None
        self.cur_chars = []
        self.total     = 0
        self.counts    = {t: 0 for t in out_map}

    @staticmethod
    def _esc(s: str) -> str:
        return (s.replace("&", "&amp;")
                  .replace("<", "&lt;")
                  .replace(">", "&gt;")
                  .replace('"', "&quot;"))

    def startElement(self, name, attrs):
        if name == "document":
            self.in_doc    = True
            self.maincat   = ""
            self.buf       = ["<document>\n"]
            self.cur_tag   = None
            self.cur_chars = []
            return
        if not self.in_doc:
            return
        self.buf.append(f"  <{name}>")
        if name == "maincat":
            self.cur_tag   = "maincat"
            self.cur_chars = []

    def characters(self, content):
        if not self.in_doc:
            return
        self.buf.append(self._esc(content))
        if self.cur_tag:
            self.cur_chars.append(content)

    def endElement(self, name):
        if not self.in_doc:
            return

        if name == "document":
            self.buf.append("</document>\n")
            self.total += 1

            if self.maincat in self.out_map:
                self.out_map[self.maincat].write("".join(self.buf))
                self.counts[self.maincat] += 1

            self.in_doc    = False
            self.buf       = []
            self.maincat   = ""
            self.cur_tag   = None
            self.cur_chars = []

            if self.total % 100_000 == 0:
                resumen = " | ".join(
                    f"{cat}: {self.counts[cat]:,}"
                    for cat in self.out_map
                )
                print(f"  Procesados: {self.total:,} | {resumen}")
            return

        self.buf.append(f"</{name}>\n")

        if name == "maincat" and self.cur_tag == "maincat":
            self.maincat   = "".join(self.cur_chars).strip()
            self.cur_tag   = None
            self.cur_chars = []


# ───────────────────────────────────────────────
class WrappedFile:
    def __init__(self, fh):
        self._fh    = fh
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


def main():
    if not XML_FILE.exists():
        print(f"ERROR: No encontrado {XML_FILE}")
        return

    print(f"Procesando {XML_FILE.name} ({XML_FILE.stat().st_size / 1e9:.1f} GB)")
    print(f"Categorías buscadas: {', '.join(sorted(TARGETS))}\n")

    handles = {cat: open(output_path(cat), "w", encoding="utf-8") for cat in TARGETS}
    try:
        for cat, fh in handles.items():
            fh.write(f'<?xml version="1.0" encoding="UTF-8"?>\n'
                     f'<preguntas categoria="{cat}">\n')

        out_map = dict(handles)
        handler = DocExtractor(out_map)

        parser = xml.sax.make_parser()
        parser.setContentHandler(handler)
        parser.setFeature(xml.sax.handler.feature_validation, False)
        parser.setFeature(xml.sax.handler.feature_namespaces, False)

        try:
            with open(XML_FILE, "rb") as raw:
                parser.parse(WrappedFile(raw))
        except Exception as e:
            print(f"\n[AVISO] Parser terminó con: {e}")
            print("Guardando lo recopilado...\n")

        for fh in handles.values():
            fh.write("</preguntas>\n")

    finally:
        for fh in handles.values():
            fh.close()

    print(f"\n{handler.total:,} documentos procesados en total.")
    for cat in sorted(TARGETS):
        out = output_path(cat)
        print(f"{cat}: {handler.counts[cat]:,}: preguntas  {out.name}")


if __name__ == "__main__":
    main()
