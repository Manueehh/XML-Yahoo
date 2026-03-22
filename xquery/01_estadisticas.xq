(:
  01_estadisticas.xq
  Estadísticas generales de las 4 categorías cargadas en eXist-db.
  Colecciones:
    /db/yahooanswers/es  → Noticias y Actualidad, Politica y Gobierno (español)
    /db/yahooanswers/it  → Notizie ed eventi, Politica e governo (italiano)
:)

let $es := collection("/db/yahooanswers/es")//document
let $it := collection("/db/yahooanswers/it")//document

return
<estadisticas fecha="{current-dateTime()}">

  <!-- ══ ESPAÑOL ══ -->
  <idioma codigo="es" nombre="Español">
    {
      for $cat in distinct-values($es/maincat)
      let $docs := $es[maincat = $cat]
      let $respuestas := count($docs//answer_item)
      order by count($docs) descending
      return
        <categoria nombre="{$cat}">
          <total_preguntas>{ count($docs) }</total_preguntas>
          <total_respuestas>{ $respuestas }</total_respuestas>
          <media_respuestas>{ format-number($respuestas div count($docs), "0.00") }</media_respuestas>
          <sin_content>{ count($docs[not(content) or content = '']) }</sin_content>
          <con_vot_date>{ count($docs[vot_date]) }</con_vot_date>
          <subcategorias>{
            for $sub in distinct-values($docs/subcat)
            order by count($docs[subcat=$sub]) descending
            return <subcat nombre="{$sub}" total="{count($docs[subcat=$sub])}"/>
          }</subcategorias>
        </categoria>
    }
    <totales>
      <preguntas>{ count($es) }</preguntas>
      <respuestas>{ count($es//answer_item) }</respuestas>
      <usuarios_unicos_preguntando>{ count(distinct-values($es/id)) }</usuarios_unicos_preguntando>
      <usuarios_unicos_respondiendo>{ count(distinct-values($es/best_id)) }</usuarios_unicos_respondiendo>
    </totales>
  </idioma>

  <!-- ══ ITALIANO ══ -->
  <idioma codigo="it" nombre="Italiano">
    {
      for $cat in distinct-values($it/maincat)
      let $docs := $it[maincat = $cat]
      let $respuestas := count($docs//answer_item)
      order by count($docs) descending
      return
        <categoria nombre="{$cat}">
          <total_preguntas>{ count($docs) }</total_preguntas>
          <total_respuestas>{ $respuestas }</total_respuestas>
          <media_respuestas>{ format-number($respuestas div count($docs), "0.00") }</media_respuestas>
          <sin_content>{ count($docs[not(content) or content = '']) }</sin_content>
          <con_vot_date>{ count($docs[vot_date]) }</con_vot_date>
          <subcategorias>{
            for $sub in distinct-values($docs/subcat)
            order by count($docs[subcat=$sub]) descending
            return <subcat nombre="{$sub}" total="{count($docs[subcat=$sub])}"/>
          }</subcategorias>
        </categoria>
    }
    <totales>
      <preguntas>{ count($it) }</preguntas>
      <respuestas>{ count($it//answer_item) }</respuestas>
      <usuarios_unicos_preguntando>{ count(distinct-values($it/id)) }</usuarios_unicos_preguntando>
      <usuarios_unicos_respondiendo>{ count(distinct-values($it/best_id)) }</usuarios_unicos_respondiendo>
    </totales>
  </idioma>

  <!-- ══ GLOBAL ══ -->
  <global>
    <total_preguntas>{ count($es) + count($it) }</total_preguntas>
    <total_respuestas>{ count($es//answer_item) + count($it//answer_item) }</total_respuestas>
  </global>

</estadisticas>
