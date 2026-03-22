(:
  02_redes_sociales.xq
  Análisis de Redes Sociales sobre las 4 categorías.
  Basado en: Shen et al. (2015) - Knowledge Sharing in Yahoo! Answers.

  Optimización: se usa XQuery 3.0 "group by" para evitar el bucle
  O(n²) que causaba timeout (5170 usuarios × 16952 docs = 87M comparaciones).
  Con group by toda la fase de conteo es O(n log n).
:)

let $es    := collection("/db/yahooanswers/es")//document
let $it    := collection("/db/yahooanswers/it")//document
let $todos := ($es, $it)

(:
  Agrupar respondedores: una sola pasada O(n log n).
  Reemplaza: for $uid in distinct-values(...) let $n := count($todos[best_id=$uid])
:)
let $resp_grp :=
  for $d in $todos
  let $uid := string($d/best_id)
  where $uid != ""
  group by $uid
  order by count($d) descending
  return <u id="{$uid}" n="{count($d)}"/>

(:
  Agrupar preguntadores: una sola pasada O(n log n).
:)
let $preg_grp :=
  for $d in $todos
  let $uid := string($d/id)
  where $uid != ""
  group by $uid
  order by count($d) descending
  return <u id="{$uid}" n="{count($d)}"/>

(: Conjuntos de IDs derivados de los grupos ya calculados :)
let $resp_ids := $resp_grp/string(@id)
let $preg_ids := $preg_grp/string(@id)

(: Simetría: intersección sobre conjuntos ya reducidos (miles, no millones) :)
let $ambas        := $preg_ids[. = $resp_ids]
let $total_unicos := count(distinct-values(($preg_ids, $resp_ids)))

return
<analisis_redes_sociales fecha="{current-dateTime()}">

  <!-- ══ 1. SIMETRÍA GLOBAL ══ -->
  <simetria>
    <descripcion>Baja simetría: pocos usuarios hacen ambas cosas (Shen 2015)</descripcion>
    <total_usuarios_distintos>{ $total_unicos }</total_usuarios_distintos>
    <solo_preguntan  total="{count($preg_ids) - count($ambas)}" porcentaje="{
      format-number((count($preg_ids) - count($ambas)) div $total_unicos * 100, '0.0')
    }%"/>
    <solo_responden  total="{count($resp_ids) - count($ambas)}" porcentaje="{
      format-number((count($resp_ids) - count($ambas)) div $total_unicos * 100, '0.0')
    }%"/>
    <preguntan_y_responden total="{count($ambas)}" porcentaje="{
      format-number(count($ambas) div $total_unicos * 100, '0.0')
    }%"/>
  </simetria>

  <!-- ══ 2. TOP 10 RESPONDEDORES GLOBALES ══ -->
  <top_respondedores descripcion="Usuarios con más 'mejor respuesta' seleccionada">{
    for $u in subsequence($resp_grp, 1, 10)
    return <usuario id="{$u/@id}" mejores_respuestas="{$u/@n}"/>
  }</top_respondedores>

  <!-- ══ 3. TOP 10 PREGUNTADORES GLOBALES ══ -->
  <top_preguntadores descripcion="Usuarios que más preguntas han publicado">{
    for $u in subsequence($preg_grp, 1, 10)
    return <usuario id="{$u/@id}" preguntas="{$u/@n}"/>
  }</top_preguntadores>

  <!-- ══ 4. CLUSTERING POR CATEGORÍA ══ -->
  <clustering descripcion="¿Los top respondedores se especializan en pocas categorías? (Shen 2015)">
    {
      (: Top 5 ya calculados — sin doble recorrido :)
      for $u in subsequence($resp_grp, 1, 5)
      let $uid     := string($u/@id)
      let $cats_es := distinct-values($es[best_id = $uid]/maincat)
      let $cats_it := distinct-values($it[best_id = $uid]/maincat)
      return
        <usuario id="{$uid}"
                 total_mejores="{$u/@n}"
                 categorias_ES="{count($cats_es)}"
                 categorias_IT="{count($cats_it)}"
                 total_categorias="{count(distinct-values(($cats_es,$cats_it)))}"/>
    }
  </clustering>

  <!-- ══ 5. PUENTES ENTRE COMUNIDADES ES ↔ IT ══ -->
  <puentes_es_it descripcion="Usuarios que responden en categorías ES e IT (bilingües/activos en ambas)">
    {
      let $resp_es := distinct-values($es/best_id)
      let $resp_it := distinct-values($it/best_id)
      let $puentes := $resp_es[. = $resp_it]
      (: Limitamos a 10 ejemplos para no generar salida masiva :)
      return
        element resumen {
          attribute total_puentes { count($puentes) },
          for $uid in subsequence($puentes, 1, 10)
          return
            element usuario {
              attribute id            { $uid },
              attribute respuestas_ES { count($es[best_id=$uid]) },
              attribute respuestas_IT { count($it[best_id=$uid]) }
            }
        }
    }
  </puentes_es_it>

  <!-- ══ 6. SIMETRÍA POR CATEGORÍA ══ -->
  <simetria_por_categoria>{
    for $cat in distinct-values($todos/maincat)
    let $docs    := $todos[maincat = $cat]
    let $preg_c  := distinct-values($docs/id)
    let $resp_c  := distinct-values($docs/best_id)
    let $ambos_c := $preg_c[. = $resp_c]
    return
      <categoria nombre="{$cat}"
                 preguntadores="{count($preg_c)}"
                 respondedores="{count($resp_c)}"
                 ambas_cosas="{count($ambos_c)}"
                 simetria="{format-number(count($ambos_c) div count(distinct-values(($preg_c,$resp_c))) * 100, '0.0')}%"/>
  }</simetria_por_categoria>

</analisis_redes_sociales>
