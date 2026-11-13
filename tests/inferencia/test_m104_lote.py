"""M1-04, tarea 4: vínculo con el LLM por la Batch API — reanudable (batch_id guardado antes de consultar), con tope de costo, lote
borrado al bajar los resultados, y sin secretos. Todo con un proveedor falso (sin red ni clave)."""
from __future__ import annotations

import json
from dataclasses import replace

import pytest

from pap.errores import PapError
from pap.inferencia.cuestionarios import Pregunta, VariableDic
from pap.inferencia.cuestionarios_lote import ParametrosLote, vincular_con_llm

from .fixtures_m104.proveedor_falso import Interrumpido, ProveedorFalso, ServidorFalso, responder_con

PREGUNTAS = [
    Pregunta("individual", "412", "¿Le hicieron la prueba de papanicolaou?", "SECCIÓN 8", 3, ["1 SI", "2 NO"]),
    Pregunta("individual", "413", "¿Le hicieron un examen de mama?", "SECCIÓN 8", 3, ["1 SI", "2 NO"]),
    Pregunta("individual", "414", "¿Cuándo fue la última vez?", "SECCIÓN 8", 3),
]
VARS = [VariableDic("REC95", "S412", "Prueba de Papanicolaou", categorias=[("1", "Sí"), ("2", "No")]),
        VariableDic("REC95", "S413", "Examen de mama"),
        VariableDic("REC95", "S999", "Algo que no está en el cuestionario")]
CUESTS = {"REC95": ["individual"]}


def _pl() -> ParametrosLote:
    return replace(ParametrosLote.desde_yaml(), sondeo_s=0.0)


def _responder():
    """El «modelo» falso: a S412 le da la 412, a S413 la 413 pero la verificación de S413 la rechaza, a S999 «ninguna»."""
    def f(p):
        if p.custom_id.startswith("vin"):
            if "S412" in p.usuario:
                return json.dumps({"id": _id_de(p.usuario, "papanicolaou")})
            if "S413" in p.usuario:
                return json.dumps({"id": _id_de(p.usuario, "examen de mama")})
            return json.dumps({"id": "ninguna"})
        return json.dumps({"coincide": "S412" in p.usuario})
    return f


def _id_de(usuario: str, fragmento: str) -> str:
    for linea in usuario.splitlines():
        if linea[:1] == "c" and fragmento in linea.lower():
            return linea.split(":")[0].strip()
    raise AssertionError(f"no hay candidato con «{fragmento}» en el prompt:\n{usuario}")


def _correr(carpeta, prov, **kw):
    return vincular_con_llm(VARS, PREGUNTAS, CUESTS, prov, carpeta, _pl(), dormir=lambda s: None, **kw)


def test_el_lote_completo_vincula_verifica_y_borra_los_dos_lotes(tmp_path):
    srv = ServidorFalso(_responder(), en_proceso_antes_de_terminar=2)
    vin = _correr(tmp_path, ProveedorFalso(srv))
    por = {(v.tabla, v.codigo): v for v in vin}
    assert por[("REC95", "S412")].pregunta_id == "individual:412" and por[("REC95", "S412")].metodo == "llm"
    assert por[("REC95", "S412")].estado == "propuesto"
    assert por[("REC95", "S413")].pregunta_id is None and por[("REC95", "S413")].motivo == "rechazada_por_verificacion"
    assert por[("REC95", "S999")].pregunta_id is None and por[("REC95", "S999")].motivo == "no_encontrada"
    assert por[("REC95", "S999")].metodo == "sin_pregunta"
    assert srv.creados == 2 and srv.vivos == 0 and len(srv.borrados) == 2          # 1 lote por etapa, ambos borrados
    est = json.loads((tmp_path / "estado_lote.json").read_text())
    assert est["etapas"]["vincular"]["borrado"] and est["etapas"]["verificar"]["borrado"]
    assert est["gasto_usd"] > 0


def test_el_batch_id_queda_guardado_antes_de_consultar_el_estado_y_la_corrida_se_reanuda(tmp_path):
    srv = ServidorFalso(_responder())
    with pytest.raises(Interrumpido):
        _correr(tmp_path, ProveedorFalso(srv, corta_en_estado=True))
    est = json.loads((tmp_path / "estado_lote.json").read_text())
    assert est["etapas"]["vincular"]["batch_id"] == "msgbatch_falso_001"         # ya estaba guardado cuando murió la consulta
    vin = _correr(tmp_path, ProveedorFalso(srv))                                   # otro proceso, mismo servidor
    assert srv.creados == 2                                                         # no creó de nuevo el primer lote (1 + el de verificar)
    assert {v.codigo: v.pregunta_id for v in vin}["S412"] == "individual:412"


def test_si_se_corta_a_la_mitad_de_los_resultados_la_reanudacion_da_lo_mismo_que_una_corrida_entera(tmp_path):
    entera = _correr(tmp_path / "a", ProveedorFalso(ServidorFalso(_responder())))
    srv = ServidorFalso(_responder())
    with pytest.raises(Interrumpido):
        _correr(tmp_path / "b", ProveedorFalso(srv, corta_tras_n_resultados=1))     # bajó 1 de 3 resultados
    parcial = (tmp_path / "b" / "resultados_vincular.jsonl").read_text().splitlines()
    assert len(parcial) == 1 and srv.borrados == []                                 # no se borra un lote a medio bajar
    reanudada = _correr(tmp_path / "b", ProveedorFalso(srv))
    filas = (tmp_path / "b" / "resultados_vincular.jsonl").read_text().splitlines()
    assert len(filas) == len({json.loads(f)["custom_id"] for f in filas}) == 3      # sin duplicados
    assert [(v.codigo, v.pregunta_id, v.motivo) for v in reanudada] == [(v.codigo, v.pregunta_id, v.motivo) for v in entera]
    assert srv.creados == 2 and srv.vivos == 0


def test_si_falla_el_borrado_el_trabajo_no_se_da_por_terminado_y_la_reanudacion_solo_borra(tmp_path):
    srv = ServidorFalso(_responder(), falla_borrado=True)
    with pytest.raises(PapError, match="borrar"):
        _correr(tmp_path, ProveedorFalso(srv))
    est = json.loads((tmp_path / "estado_lote.json").read_text())
    assert est["etapas"]["vincular"]["borrado"] is False and "verificar" not in est["etapas"]
    srv.falla_borrado = False
    _correr(tmp_path, ProveedorFalso(srv))
    assert srv.creados == 2 and srv.vivos == 0


def test_un_lote_que_pasa_el_tope_no_se_crea(tmp_path):
    srv = ServidorFalso(_responder())
    pl = replace(_pl(), tope_lote_usd=0.000001)
    with pytest.raises(PapError, match="tope"):
        vincular_con_llm(VARS, PREGUNTAS, CUESTS, ProveedorFalso(srv), tmp_path, pl, dormir=lambda s: None)
    assert srv.creados == 0


def test_un_id_que_el_modelo_inventa_se_trata_como_ninguna_y_no_como_vinculo(tmp_path):
    srv = ServidorFalso(responder_con({"S412": {"id": "c99"}}))
    vin = _correr(tmp_path, ProveedorFalso(srv))
    por = {v.codigo: v for v in vin}
    assert por["S412"].pregunta_id is None and por["S412"].motivo == "respuesta_invalida"


def test_las_peticiones_solo_llevan_textos_publicos_y_no_hay_secretos_en_los_archivos(tmp_path, monkeypatch):
    monkeypatch.setenv("PAP_ANTHROPIC_BATCH_KEY", "valor-secreto-de-prueba-1234")
    srv = ServidorFalso(_responder())
    _correr(tmp_path, ProveedorFalso(srv))
    for ruta in tmp_path.rglob("*"):
        if ruta.is_file():
            t = ruta.read_text(encoding="utf-8")
            assert "valor-secreto-de-prueba-1234" not in t and "api-key" not in t.lower()
    enviado = " ".join(p.usuario + p.sistema for lote in [srv.lotes.values()] for ps in lote for p in ps) if srv.vivos else ""
    assert enviado == ""                                                            # nada quedó vivo en el servicio


def test_el_estado_de_otra_corrida_no_se_mezcla_con_esta(tmp_path):
    srv = ServidorFalso(_responder())
    with pytest.raises(Interrumpido):
        _correr(tmp_path, ProveedorFalso(srv, corta_en_estado=True))
    with pytest.raises(PapError, match="otra corrida"):
        vincular_con_llm(VARS[:1], PREGUNTAS, CUESTS, ProveedorFalso(srv), tmp_path, _pl(), dormir=lambda s: None)


def test_un_vinculo_rechazado_por_la_verificacion_guarda_la_pregunta_que_eligio_el_modelo(tmp_path):
    """Hallazgo 6: sin la pregunta elegida los rechazos no se pueden auditar."""
    vin = _correr(tmp_path, ProveedorFalso(ServidorFalso(_responder())))
    por = {v.codigo: v for v in vin}
    assert por["S413"].motivo == "rechazada_por_verificacion" and por["S413"].pregunta_id is None
    assert "individual:413" in por["S413"].evidencia and "rechaz" in por["S413"].evidencia
    import polars as pl
    from pap.inferencia.cuestionarios import tabla_de_vinculos
    df = tabla_de_vinculos(vin, PREGUNTAS)
    assert "individual:413" in df.filter(pl.col("codigo") == "S413")["evidencia"][0]


def test_si_la_verificacion_viene_ilegible_se_guarda_igual_la_pregunta_elegida(tmp_path):
    def f(p):
        if p.custom_id.startswith("ver"):
            return "no es json"
        return _responder()(p)
    por = {v.codigo: v for v in _correr(tmp_path, ProveedorFalso(ServidorFalso(f)))}
    assert por["S412"].motivo == "error_del_lote" and "individual:412" in por["S412"].evidencia


def test_una_respuesta_invalida_guarda_lo_que_dijo_el_modelo(tmp_path):
    srv = ServidorFalso(responder_con({"S412": {"id": "c99"}}))
    por = {v.codigo: v for v in _correr(tmp_path, ProveedorFalso(srv))}
    assert por["S412"].motivo == "respuesta_invalida" and "c99" in por["S412"].evidencia


def _pl_ver(**kw):
    return replace(_pl(), **kw)


def _peticion_de_verificar(pregunta, pl):
    from pap.inferencia.cuestionarios_lote import peticiones_verificar
    v = VariableDic("REC43", "H37M", "Tomó ibuprofeno")
    [p], _ = peticiones_verificar({("REC43", "H37M"): pregunta.id}, {("REC43", "H37M"): v}, {pregunta.id: pregunta}, pl)
    return p


def test_la_verificacion_muestra_todas_las_opciones_de_la_pregunta_hasta_opciones_max(tmp_path):
    ops = [f"{chr(65 + i)} OPCION{i:02d}" for i in range(15)]
    q = Pregunta("salud", "471B", "¿Qué le dieron para la fiebre? CIRCULE TODO LO MENCIONADO", "S", 3, ops)
    p = _peticion_de_verificar(q, _pl_ver(opciones_en_prompt=8))
    assert all(f"OPCION{i:02d}" in p.usuario for i in range(15))               # no se corta en opciones_en_prompt (8)
    from pap.inferencia.cuestionarios import _config
    tope = int(_config()["opciones_max"]["valor"])
    q2 = Pregunta("salud", "9", "¿Cuál?", "S", 3, [f"OP{i:03d}X" for i in range(tope + 10)])
    p2 = _peticion_de_verificar(q2, _pl())
    assert f"OP{tope - 1:03d}X" in p2.usuario and f"OP{tope:03d}X" not in p2.usuario


def test_la_instruccion_de_verificar_admite_una_opcion_de_respuesta_multiple_y_sigue_diciendo_false_si_dudas():
    from pap.inferencia.cuestionarios_lote import SISTEMA_VERIFICAR
    t = SISTEMA_VERIFICAR.lower()
    assert "respuesta múltiple" in t and "una de las opciones" in t and "sí coincide" in t
    assert "si dudas, responde false" in t


def test_la_pasada_de_vincular_sigue_cortando_las_opciones_en_prompt():
    from pap.inferencia.cuestionarios import Candidatos
    from pap.inferencia.cuestionarios_lote import peticiones_vincular
    ops = [f"{i} OPCION{i:02d}" for i in range(15)]
    q = Pregunta("individual", "412", "¿Le hicieron la prueba?", "S", 3, ops)
    [p], _ = peticiones_vincular([VARS[0]], Candidatos([q]), CUESTS, _pl_ver(opciones_en_prompt=8))
    assert "OPCION07" in p.usuario and "OPCION08" not in p.usuario
