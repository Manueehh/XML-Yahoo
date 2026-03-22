# Trabajo XML — Yahoo Answers Analysis

Análisis de preguntas del dataset **Yahoo! Answers (Oct. 2007)** filtradas por categoría temática, usando **eXist-db** como base de datos documental y **XQuery** para el análisis.

**Categorías:**
| Idioma | Categoría 1 | Categoría 2 | Responsable |
|--------|-------------|-------------|-------------|
| Español 🇪🇸 | Noticias y Actualidad | Política y Gobierno | Manuel Avilés |
| Italiano 🇮🇹 | Notizie ed eventi | Politica e governo | Matteo Amagliani |

---

## Estructura del proyecto

```
XML-Yahoo/
├── src/
│   ├── extraer_categorias.py       # Extrae categorías únicas del XML original (12GB)
│   └── extraer_preguntas.py        # Extrae preguntas por categoría → data/preguntas_*.xml
│
├── existdb/
│   ├── cargar_existdb.py           # Carga los 4 XML en eXist-db (REST API)
│   └── ejecutar_xquery.py          # Ejecuta consultas .xq y muestra/guarda resultados
│
├── xquery/
│   ├── 01_estadisticas.xq          # Conteos, subcategorías, media de respuestas
│   ├── 02_redes_sociales.xq        # Análisis de redes: simetría, usuarios top, clustering
│   ├── 03_calidad_datos.xq         # Campos vacíos, anomalías, consistencia de fechas
│   └── 04_consultas_avanzadas.xq   # Comparativa ES/IT, países, curiosidades
│
├── xsd/
│   └── yahoo_answers.xsd           # XSD con la estructura de los XML del corpus
│
├── xslt/
│   ├── es_html.xsl                 # Transforma los XML en español a HTML
│   └── it_html.xsl                 # Transforma los XML en italiano a HTML
│
├── data/
│   ├── FullOct2007.xml             # Dataset original (12 GB, NO incluido en el repo)
│   ├── categorias.txt              # Listado de categorías encontradas
│   └── preguntas_*.xml             # Preguntas extraídas por categoría (4 ficheros)
│
└── README.md
```

---

## Requisitos

- **Python 3.10+**
- **Java 8+** (necesario para eXist-db)
- **eXist-db 6.x** — ver instalación abajo
- Librería Python: `pip install requests`

---

## Paso 1 — Instalar eXist-db

1. Descargar el instalador desde: https://github.com/eXist-db/exist/releases/latest
   - Elegir el fichero `.jar` (p.ej. `eXist-db-setup-6.x.x.jar`)

2. Ejecutar el instalador:
   ```bash
   java -jar eXist-db-setup-6.x.x.jar
   ```
   Seguir el asistente gráfico. Por defecto se instala en `~/eXist-db/`.

3. Arrancar eXist-db:
   ```bash
   # Linux / macOS
   ~/eXist-db/bin/startup.sh

   # Windows
   %USERPROFILE%\eXist-db\bin\startup.bat
   ```

4. Esperar ~30 segundos y abrir en el navegador:
   - Panel de administración: http://localhost:8080/exist/
   - Editor XQuery (eXide): http://localhost:8080/exist/apps/eXide/

   El usuario por defecto es `admin` con contraseña vacía (se puede cambiar en el panel).

---

## Paso 2 — Extraer los XML del corpus (si no los tienes ya)

Si partes del fichero original `FullOct2007.xml` (12 GB):

```bash
# Opcional: ver todas las categorías disponibles
python src/extraer_categorias.py

# Extraer los 4 XML de las categorías del trabajo
python src/extraer_preguntas.py
```

Esto genera en `data/`:
- `preguntas_noticias_y_actualidad.xml`
- `preguntas_política_y_gobierno.xml`
- `preguntas_notizie_ed_eventi.xml`
- `preguntas_politica_e_governo.xml`

---

## Paso 3 — Cargar los XML en eXist-db

Con eXist-db corriendo:

```bash
pip install requests
python existdb/cargar_existdb.py
```

Esto crea en eXist-db:
```
/db/yahooanswers/
    es/   ← preguntas_noticias_y_actualidad.xml
          ← preguntas_política_y_gobierno.xml
    it/   ← preguntas_notizie_ed_eventi.xml
          ← preguntas_politica_e_governo.xml
```

Si tu contraseña de admin no es vacía:
```bash
python existdb/cargar_existdb.py --user admin --password tu_contraseña
```

---

## Paso 4 — Ejecutar las consultas XQuery

### Opción A — Desde la línea de comandos

```bash
# Una consulta concreta
python existdb/ejecutar_xquery.py xquery/01_estadisticas.xq

# Todas, guardando resultados en resultados/
python existdb/ejecutar_xquery.py --todos --output resultados/
```

### Opción B — Desde eXide (interfaz web)

1. Abrir http://localhost:8080/exist/apps/eXide/
2. Copiar el contenido de cualquier fichero `.xq` y pegar en el editor
3. Pulsar `Run` (▶)

---

## Validar XML con el XSD

Para comprobar que los XML están bien formados según el esquema:

```bash
pip install lxml

python - << 'EOF'
from lxml import etree
schema = etree.XMLSchema(etree.parse("xsd/yahoo_answers.xsd"))
doc    = etree.parse("data/preguntas_noticias_y_actualidad.xml")
if schema.validate(doc):
    print("XML valido")
else:
    for e in schema.error_log:
        print("Linea", e.line, "-", e.message)
EOF
```

## Transformar XML a HTML con XSLT

Usando Saxon (XSLT 1.0 está soportado también por `lxml`):

```bash
python - << 'EOF'
from lxml import etree

xslt  = etree.parse("xslt/es_html.xsl")
trans = etree.XSLT(xslt)

doc    = etree.parse("data/preguntas_noticias_y_actualidad.xml")
result = trans(doc)
with open("noticias_y_actualidad.html", "wb") as f:
    f.write(bytes(result))
print("HTML generado")
EOF
```

Hacer lo mismo con los otros tres XML cambiando el fichero de entrada y el XSLT (`it_html.xsl` para los italianos).

---

## Consultas incluidas

| Fichero | Qué analiza |
|---------|-------------|
| `01_estadisticas.xq` | Total preguntas/respuestas, media de respuestas, subcategorías, % sin `content` |
| `02_redes_sociales.xq` | Simetría pregunta/respuesta, top respondedores, clustering por categoría, puentes ES↔IT |
| `03_calidad_datos.xq` | Campos vacíos, longitudes, fechas inconsistentes, anomalías, velocidad de resolución |
| `04_consultas_avanzadas.xq` | Comparativa ES vs IT, países de origen, palabras clave, autorespuestas |

---

## Datos del corpus

| Fichero | Preguntas | Idioma |
|---------|-----------|--------|
| `preguntas_noticias_y_actualidad.xml` | 674 | Español |
| `preguntas_política_y_gobierno.xml` | 12.976 | Español |
| `preguntas_notizie_ed_eventi.xml` | 1.184 | Italiano |
| `preguntas_politica_e_governo.xml` | 2.118 | Italiano |
| **Total** | **16.952** | |

---

## Referencias

- Shen et al. (2015). *Knowledge Sharing in the Online Social Network of Yahoo! Answers*. IEEE Trans. on Computers.
- Adamic et al. (2008). *Knowledge Sharing and Yahoo Answers: Everyone Knows Something*. WWW 2008.
- Shah et al. (2010). *Evaluating and Predicting Answer Quality in Community QA*. SIGIR 2010.
