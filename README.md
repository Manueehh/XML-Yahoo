# Trabajo XML — Yahoo Answers Analysis

Análisis de preguntas del dataset **Yahoo! Answers (Oct. 2007)** filtradas por categoría temática.

## Estructura del proyecto

```
Trabajo XML/
├── src/
│   ├── extraer_categorias.py   # Extrae todas las categorías únicas del XML
│   └── extraer_preguntas.py    # Extrae preguntas por categoría → data/preguntas_*.xml
├── data/
│   ├── FullOct2007.xml         # Dataset original (12 GB, NO incluido en el repo)
│   ├── categorias.txt          # Listado de categorías encontradas
│   └── preguntas_*.xml         # Preguntas extraídas por categoría
└── README.md
```

## Requisitos

- Python 3.10+
- No se necesitan librerías externas para la extracción (solo stdlib)

## Uso

### 1. Extraer categorías

```bash
python src/extraer_categorias.py
```

Genera `data/categorias.txt` con todas las combinaciones únicas de `maincat / subcat / cat`.

### 2. Extraer preguntas

Edita la variable `TARGETS` en `src/extraer_preguntas.py` con las categorías deseadas:

```python
TARGETS = {
    "Política y Gobierno",   # español
    "Noticias y Actualidad", # español
    "Politica e governo",    # italiano
    "Notizie ed eventi",     # italiano
}
```

Luego ejecuta:

```bash
python src/extraer_preguntas.py
```

Genera un fichero `data/preguntas_<categoria>.xml` por cada categoría.

## Dataset

El fichero `FullOct2007.xml` es el dataset público de Yahoo! Answers del año 2007.
Pesa ~12 GB y no está incluido en este repositorio. Debe colocarse en `data/`.
