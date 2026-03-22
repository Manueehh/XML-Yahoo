(:
  04_consultas_avanzadas.xq
  Consultas temáticas, curiosidades y comparativas ES vs IT.

  Optimización: se usa XQuery 3.0 "group by" para reemplazar los bucles
  O(n²) y se pre-computan conteos en una sola pasada por la colección.
:)

let $es    := collection("/db/yahooanswers/es")//document
let $it    := collection("/db/yahooanswers/it")//document
let $todos := ($es, $it)

(:
  Pre-calcular el número de respuestas por documento en una sola pasada.
  Así la sección 1 (mas_respondidas) no tiene que re-contar nodos
  durante la ordenación de cada categoría.
:)
let $docs_con_n :=
  for $d in $todos
  return <d cat="{$d/maincat}"
            uri="{$d/uri}"
            n="{count($d/nbestanswers/answer_item)}"
            qlang="{$d/qlang}"
            subj="{normalize-space($d/subject)}"/>

(:
  Pre-calcular distribución de países con group by (O(n log n)).
  Reemplaza: for $p in distinct-values(...) let $n := count($todos[qintl=$p])
:)
let $paises_grp :=
  for $d in $todos
  let $p := string($d/qintl)
  where $p != ""
  group by $p
  order by count($d) descending
  return <pais codigo="{$p}" preguntas="{count($d)}"/>

return
<consultas_avanzadas fecha="{current-dateTime()}">

  <!-- ══ 1. PREGUNTAS MÁS RESPONDIDAS (top 3 por categoría) ══ -->
  <mas_respondidas>{
    for $cat in distinct-values($todos/maincat)
    let $cat_docs := $docs_con_n[@cat = $cat]
    let $ordenados :=
      for $d in $cat_docs
      order by xs:integer($d/@n) descending
      return $d
    return
      <categoria nombre="{$cat}">{
        for $d in subsequence($ordenados, 1, 3)
        return
          <pregunta uri="{$d/@uri}"
                    num_respuestas="{$d/@n}"
                    idioma="{$d/@qlang}">
            { string($d/@subj) }
          </pregunta>
      }</categoria>
  }</mas_respondidas>

  <!-- ══ 2. COMPARATIVA ES vs IT ══ -->
  <comparativa_es_it>
    <descripcion>Diferencias entre la comunidad hispanohablante e italohablante</descripcion>
    <item metrica="Media respuestas/pregunta"
          ES="{format-number(count($es//answer_item) div count($es), '0.00')}"
          IT="{format-number(count($it//answer_item) div count($it), '0.00')}"/>
    <item metrica="Media longitud bestanswer (chars)"
          ES="{format-number(avg($es/string-length(bestanswer)), '0.0')}"
          IT="{format-number(avg($it/string-length(bestanswer)), '0.0')}"/>
    <item metrica="% sin campo content"
          ES="{format-number(count($es[not(content) or content='']) div count($es) * 100, '0.0')}%"
          IT="{format-number(count($it[not(content) or content='']) div count($it) * 100, '0.0')}%"/>
    <item metrica="Usuarios únicos preguntando"
          ES="{count(distinct-values($es/id))}"
          IT="{count(distinct-values($it/id))}"/>
    <item metrica="Usuarios únicos respondiendo"
          ES="{count(distinct-values($es/best_id))}"
          IT="{count(distinct-values($it/best_id))}"/>
    <item metrica="% resueltas el mismo día"
          ES="{format-number(count($es[number(res_date) - number(date) lt 86400
                                       and number(res_date) >= number(date)]) div count($es) * 100, '0.0')}%"
          IT="{format-number(count($it[number(res_date) - number(date) lt 86400
                                       and number(res_date) >= number(date)]) div count($it) * 100, '0.0')}%"/>
  </comparativa_es_it>

  <!-- ══ 3. DISTRIBUCIÓN POR PAÍS DE ORIGEN (qintl) ══ -->
  <paises_de_origen>{
    for $p in $paises_grp
    return $p
  }</paises_de_origen>

  <!-- ══ 4. POLÍTICA: palabras clave curiosas ══ -->
  <temas_politica>
    <descripcion>Preguntas de Política que mencionan términos en subject</descripcion>
    {
      let $pol := $todos[maincat = "Política y Gobierno" or maincat = "Politica e governo"]
      for $termino in ("inmigración", "inmigrante", "immigrazione", "immigrante",
                       "ley", "legge", "presidente", "governo", "gobierno")
      let $menciones := $pol[contains(lower-case(subject), $termino)]
      where count($menciones) > 0
      return <termino texto="{$termino}" menciones="{count($menciones)}"/>
    }
  </temas_politica>

  <!-- ══ 5. CURIOSIDAD: preguntas sin ninguna respuesta en nbestanswers ══ -->
  <sin_respuestas>
    {
      let $vacias := $docs_con_n[@n = "0"]  (: usar datos pre-calculados :)
      return <resultado total="{count($vacias)}">{
        for $d in subsequence($vacias, 1, 3)
        return <doc uri="{$d/@uri}" cat="{$d/@cat}">{ string($d/@subj) }</doc>
      }</resultado>
    }
  </sin_respuestas>

  <!-- ══ 6. CURIOSIDAD: preguntas donde el autor se respondió a sí mismo ══ -->
  <autorespuestas>
    <descripcion>Preguntas donde id == best_id (el autor eligió su propia respuesta como mejor)</descripcion>
    {
      let $auto := $todos[id = best_id]
      return <resultado total="{count($auto)}"
                        porcentaje="{format-number(count($auto) div count($todos) * 100, '0.0')}%">{
        for $d in subsequence($auto, 1, 5)
        return <doc uri="{$d/uri}" usuario="{$d/id}" cat="{$d/maincat}">{ $d/subject/text() }</doc>
      }</resultado>
    }
  </autorespuestas>

</consultas_avanzadas>
