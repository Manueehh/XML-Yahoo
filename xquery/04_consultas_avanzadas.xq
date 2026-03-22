let $es    := collection("/db/yahooanswers/es")//document
let $it    := collection("/db/yahooanswers/it")//document
let $todos := ($es, $it)

return
<consultas_avanzadas fecha="{current-dateTime()}">

  <comparativa_es_it>
    <item metrica="Media respuestas/pregunta"
          ES="{format-number(count($es//answer_item) div count($es), '0.00')}"
          IT="{format-number(count($it//answer_item) div count($it), '0.00')}"/>
    <item metrica="Media longitud bestanswer"
          ES="{format-number(avg($es/string-length(bestanswer)), '0.0')}"
          IT="{format-number(avg($it/string-length(bestanswer)), '0.0')}"/>
    <item metrica="Porcentaje sin content"
          ES="{format-number(count($es[not(content) or content='']) div count($es) * 100, '0.0')}%"
          IT="{format-number(count($it[not(content) or content='']) div count($it) * 100, '0.0')}%"/>
    <item metrica="Usuarios unicos preguntando"
          ES="{count(distinct-values($es/id))}"
          IT="{count(distinct-values($it/id))}"/>
    <item metrica="Usuarios unicos respondiendo"
          ES="{count(distinct-values($es/best_id))}"
          IT="{count(distinct-values($it/best_id))}"/>
    <item metrica="Porcentaje resueltas el mismo dia"
          ES="{format-number(count($es[number(res_date) - number(date) lt 86400 and number(res_date) >= number(date)]) div count($es) * 100, '0.0')}%"
          IT="{format-number(count($it[number(res_date) - number(date) lt 86400 and number(res_date) >= number(date)]) div count($it) * 100, '0.0')}%"/>
  </comparativa_es_it>

  <temas_politica>{
    let $pol := $todos[maincat = "Política y Gobierno" or maincat = "Politica e governo"]
    for $termino in ("inmigracion", "inmigrante", "immigrazione", "immigrante",
                     "ley", "legge", "presidente", "governo", "gobierno")
    let $n := count($pol[contains(lower-case(subject), $termino)])
    where $n > 0
    return <termino texto="{$termino}" menciones="{$n}"/>
  }</temas_politica>

  <sin_respuestas>{
    let $vacias := $todos[count(nbestanswers/answer_item) = 0]
    return <resultado total="{count($vacias)}">
      {
        for $d in subsequence($vacias, 1, 3)
        return <doc uri="{$d/uri}" cat="{$d/maincat}">{ string($d/subject) }</doc>
      }
    </resultado>
  }</sin_respuestas>

</consultas_avanzadas>
