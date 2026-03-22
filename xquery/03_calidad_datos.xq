(:
  03_calidad_datos.xq
  Análisis de Calidad de Datos de las 4 categorías.
  Detecta: campos vacíos, inconsistencias, anomalías, longitudes.
:)

let $es    := collection("/db/yahooanswers/es")//document
let $it    := collection("/db/yahooanswers/it")//document
let $todos := ($es, $it)

return
<calidad_datos fecha="{current-dateTime()}">

  <!-- ══ 1. COMPLETITUD DE CAMPOS ══ -->
  <completitud>
    {
      for $campo in ("content", "vot_date")
      let $presentes := count($todos[*[name()=$campo] and *[name()=$campo] != ''])
      let $ausentes  := count($todos) - $presentes
      return
        <campo nombre="{$campo}"
               total="{count($todos)}"
               presentes="{$presentes}"
               ausentes="{$ausentes}"
               porcentaje_ausentes="{format-number($ausentes div count($todos) * 100, '0.0')}%"/>
    }
  </completitud>

  <!-- ══ 2. LONGITUDES DE TEXTO ══ -->
  <longitudes>
    <campo nombre="subject">
      <min>{ min($todos/string-length(subject)) }</min>
      <max>{ max($todos/string-length(subject)) }</max>
      <media>{ format-number(avg($todos/string-length(subject)), "0.0") }</media>
    </campo>
    <campo nombre="bestanswer">
      <min>{ min($todos/string-length(bestanswer)) }</min>
      <max>{ max($todos/string-length(bestanswer)) }</max>
      <media>{ format-number(avg($todos/string-length(bestanswer)), "0.0") }</media>
    </campo>
    <campo nombre="num_respuestas">
      <min>{ min($todos/count(nbestanswers/answer_item)) }</min>
      <max>{ max($todos/count(nbestanswers/answer_item)) }</max>
      <media>{ format-number(avg($todos/count(nbestanswers/answer_item)), "0.0") }</media>
    </campo>
  </longitudes>

  <!-- ══ 3. INCONSISTENCIAS DE FECHAS ══ -->
  <consistencia_fechas>
    <descripcion>Documentos donde date > res_date (fecha resolución anterior a publicación)</descripcion>
    {
      let $malos := $todos[xs:long(date) > xs:long(res_date)]
      return
        <resultado total="{count($malos)}">{
          for $d in subsequence($malos, 1, 5)
          return <doc uri="{$d/uri}" date="{$d/date}" res_date="{$d/res_date}" cat="{$d/maincat}"/>
        }</resultado>
    }
  </consistencia_fechas>

  <!-- ══ 4. ANOMALÍAS ══ -->
  <anomalias>

    <bestanswer_muy_corto umbral_chars="20">{
      let $cortos := $todos[string-length(bestanswer) lt 20]
      return <resultado total="{count($cortos)}">{
        for $d in subsequence($cortos, 1, 5)
        return <doc uri="{$d/uri}" cat="{$d/maincat}" bestanswer="{$d/bestanswer}"/>
      }</resultado>
    }</bestanswer_muy_corto>

    <una_sola_respuesta>{
      let $unica := $todos[count(nbestanswers/answer_item) = 1]
      return <resultado total="{count($unica)}"
                        porcentaje="{format-number(count($unica) div count($todos) * 100, '0.0')}%"/>
    }</una_sola_respuesta>

    <subject_muy_corto umbral_chars="10">{
      let $cortos := $todos[string-length(subject) lt 10]
      return <resultado total="{count($cortos)}">{
        for $d in subsequence($cortos, 1, 5)
        return <doc uri="{$d/uri}" cat="{$d/maincat}" subject="{$d/subject}"/>
      }</resultado>
    }</subject_muy_corto>

  </anomalias>

  <!-- ══ 5. RESUELTAS EL MISMO DÍA ══ -->
  <velocidad_resolucion>
    {
      let $mismo_dia := $todos[
        xs:long(res_date) - xs:long(date) lt 86400
        and xs:long(res_date) >= xs:long(date)
      ]
      return
        <mismo_dia total="{count($mismo_dia)}"
                   porcentaje="{format-number(count($mismo_dia) div count($todos) * 100, '0.0')}%"/>
    }
    {
      let $una_hora := $todos[
        xs:long(res_date) - xs:long(date) lt 3600
        and xs:long(res_date) >= xs:long(date)
      ]
      return
        <menos_de_una_hora total="{count($una_hora)}"
                           porcentaje="{format-number(count($una_hora) div count($todos) * 100, '0.0')}%"/>
    }
  </velocidad_resolucion>

  <!-- ══ 6. CALIDAD POR CATEGORÍA ══ -->
  <resumen_por_categoria>{
    for $cat in distinct-values($todos/maincat)
    let $docs := $todos[maincat = $cat]
    return
      <categoria nombre="{$cat}"
                 total="{count($docs)}"
                 sin_content="{count($docs[not(content) or content=''])}"
                 pct_sin_content="{format-number(count($docs[not(content) or content='']) div count($docs) * 100,'0.0')}%"
                 bestanswer_media_chars="{format-number(avg($docs/string-length(bestanswer)),'0.0')}"
                 media_respuestas="{format-number(avg($docs/count(nbestanswers/answer_item)),'0.00')}"/>
  }</resumen_por_categoria>

</calidad_datos>
