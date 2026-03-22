<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">

  <xsl:output method="html" encoding="UTF-8" indent="yes"/>

  <xsl:template match="/">
    <html lang="es">
      <head>
        <meta charset="UTF-8"/>
        <title>Yahoo Answers - <xsl:value-of select="/preguntas/@categoria"/></title>
        <style>
          body {
            font-family: Arial, sans-serif;
            background: #f4f4f4;
            margin: 0;
            padding: 20px;
            color: #222;
          }
          h1 {
            background: #1a56a0;
            color: white;
            padding: 16px 24px;
            margin: 0 0 24px 0;
            border-radius: 6px;
          }
          .resumen {
            background: #dbeafe;
            border: 1px solid #93c5fd;
            padding: 12px 20px;
            border-radius: 6px;
            margin-bottom: 24px;
          }
          .documento {
            background: white;
            border: 1px solid #ddd;
            border-radius: 6px;
            margin-bottom: 20px;
            padding: 16px 20px;
          }
          .pregunta {
            font-size: 1.05em;
            font-weight: bold;
            color: #1a56a0;
            margin-bottom: 8px;
          }
          .detalle {
            font-size: 0.9em;
            color: #555;
            margin-bottom: 10px;
            font-style: italic;
          }
          .mejor-respuesta {
            background: #f0fdf4;
            border-left: 4px solid #22c55e;
            padding: 10px 14px;
            margin-bottom: 10px;
            font-size: 0.9em;
          }
          .mejor-respuesta span {
            font-size: 0.75em;
            font-weight: bold;
            color: #16a34a;
            display: block;
            margin-bottom: 4px;
            text-transform: uppercase;
          }
          .otras details {
            margin-top: 8px;
          }
          .otras summary {
            cursor: pointer;
            font-size: 0.85em;
            color: #1a56a0;
          }
          .respuesta {
            background: #f9f9f9;
            border: 1px solid #e5e7eb;
            padding: 8px 12px;
            margin: 4px 0;
            font-size: 0.85em;
            border-radius: 4px;
          }
          .meta {
            font-size: 0.78em;
            color: #888;
            margin-top: 10px;
            border-top: 1px solid #eee;
            padding-top: 8px;
          }
        </style>
      </head>
      <body>
        <h1>Yahoo Answers - <xsl:value-of select="/preguntas/@categoria"/></h1>

        <div class="resumen">
          <strong>Total de preguntas:</strong> <xsl:value-of select="count(//document)"/>
        </div>

        <xsl:apply-templates select="//document"/>
      </body>
    </html>
  </xsl:template>

  <xsl:template match="document">
    <div class="documento">
      <div class="pregunta">
        <xsl:value-of select="subject"/>
      </div>

      <xsl:if test="content and content != ''">
        <div class="detalle">
          <xsl:value-of select="content"/>
        </div>
      </xsl:if>

      <div class="mejor-respuesta">
        <span>Mejor respuesta</span>
        <xsl:value-of select="bestanswer"/>
      </div>

      <xsl:if test="count(nbestanswers/answer_item) > 1">
        <div class="otras">
          <details>
            <summary>
              Ver otras respuestas (<xsl:value-of select="count(nbestanswers/answer_item) - 1"/>)
            </summary>
            <xsl:for-each select="nbestanswers/answer_item">
              <xsl:if test=". != ../../bestanswer">
                <div class="respuesta">
                  <xsl:value-of select="."/>
                </div>
              </xsl:if>
            </xsl:for-each>
          </details>
        </div>
      </xsl:if>

      <div class="meta">
        Categoria: <xsl:value-of select="subcat"/> |
        Autor: <xsl:value-of select="id"/> |
        Mejor respuesta de: <xsl:value-of select="best_id"/> |
        Idioma: <xsl:value-of select="language"/>
      </div>
    </div>
  </xsl:template>

</xsl:stylesheet>
