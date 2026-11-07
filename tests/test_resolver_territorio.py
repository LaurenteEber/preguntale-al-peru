"""S1-02 — Resolver territorial determinista: texto/ubigeo/ámbito → Resuelto o Aclaracion.

Usa las dimensiones reconstruidas (dim_ubigeo_historico, dim_ambito). Si faltan, las pruebas FALLAN (agents.md §8)."""
import json
import re
import unicodedata
from pathlib import Path

import pytest
import yaml

from pap.config import Rutas
from pap.motor.territorio import Aclaracion, Resuelto, _config, resolver
from pap.motor.validador.contexto import cargar_contexto

from conftest import RAIZ_REAL


@pytest.fixture(scope="module")
def ctx():
    raiz = Rutas(RAIZ_REAL).raiz
    for t in ("dim_ubigeo_historico", "dim_ambito"):
        p = raiz / "biblioteca" / "dimensiones" / f"{t}.parquet"
        assert p.exists(), f"falta {p}: reconstruir con `pap construir territorio`"
    return cargar_contexto(raiz, con_cubo=False)


def sin_tildes(s):
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()


def texto(ctx, t):
    return resolver({"texto": t}, ctx)


def etiquetas(a):
    return [o["etiqueta"] for o in a.opciones]


# ------------------------------------------------------------------ resolución directa

DIRECTOS = [
    # texto, nivel, id, nombre_mostrado
    ("departamento de Huancavelica", "departamento", "09", "Huancavelica"),
    ("Departamento de huancavelica", "departamento", "09", "Huancavelica"),
    ("región Huancavelica", "departamento", "09", "Huancavelica"),
    ("provincia de Huancavelica", "provincia", "090100", "Huancavelica"),
    ("distrito de Huancavelica", "distrito", "090101", "Huancavelica"),
    ("departamento de Puno", "departamento", "21", "Puno"),
    ("provincia de Melgar", "provincia", "210800", "Melgar"),
    ("Melgar", "provincia", "210800", "Melgar"),
    ("Ayaviri, Melgar", "distrito", "210801", "Ayaviri"),
    ("ayaviri, melgar", "distrito", "210801", "Ayaviri"),
    ("Ayaviri, Puno", "distrito", "210801", "Ayaviri"),
    ("Puno, Ayaviri", "distrito", "210801", "Ayaviri"),
    ("Melgar, Ayaviri", "distrito", "210801", "Ayaviri"),
    ("Ayaviri, Melgar, Puno", "distrito", "210801", "Ayaviri"),
    ("Puno, Melgar, Ayaviri", "distrito", "210801", "Ayaviri"),
    ("Ayaviri, provincia de Melgar, Puno", "distrito", "210801", "Ayaviri"),
    ("Ayaviri, Yauyos", "distrito", "151004", "Ayaviri"),
    ("Ayaviri, Lima", "distrito", "151004", "Ayaviri"),
    ("distrito de Ayaviri, Melgar", "distrito", "210801", "Ayaviri"),
    ("San Juan de Lurigancho", "distrito", "150132", "San Juan de Lurigancho"),
    ("san juan de lurigancho", "distrito", "150132", "San Juan de Lurigancho"),
    ("Alto Trujillo", "distrito", "130112", "Alto Trujillo"),
    ("Santa Rosa, Melgar", "distrito", "210808", "Santa Rosa"),
    ("San Martin de Porres", "distrito", "150135", "San Martín de Porres"),
    ("provincia de Lima", "provincia", "150100", "Lima"),
    ("distrito de Lima", "distrito", "150101", "Lima"),
    ("departamento de Lima", "departamento", "15", "Lima"),
    ("región de Lima", "departamento", "15", "Lima"),
    ("provincia del Callao", "provincia", "070100", "Callao"),
    ("distrito del Callao", "distrito", "070101", "Callao"),
    ("Callao Cercado", "distrito", "070101", "Callao"),
]


@pytest.mark.parametrize("t,nivel,id_,nombre", DIRECTOS)
def test_resuelve_directo(ctx, t, nivel, id_, nombre):
    r = texto(ctx, t)
    assert isinstance(r, Resuelto), r
    assert (r.nivel, r.id, r.nombre_mostrado) == (nivel, id_, nombre)


def test_resuelto_distrito_completo(ctx):
    r = texto(ctx, "Ayaviri, Melgar")
    assert r.ubigeo == "210801"
    assert r.nombre_completo == "Ayaviri (Melgar, Puno)"
    assert (r.departamento, r.provincia) == ("Puno", "Melgar")
    assert r.ambito_lima is None and r.provisional is False
    d = r.a_dict()
    assert d["id"] == "210801" and d["nombre_completo"] == "Ayaviri (Melgar, Puno)"


def test_resuelto_departamento_y_provincia(ctx):
    d = texto(ctx, "departamento de Huancavelica")
    assert (d.ubigeo, d.departamento, d.provincia, d.nombre_completo) == ("090000", "Huancavelica", None, "Huancavelica")
    p = texto(ctx, "provincia de Melgar")
    assert (p.ubigeo, p.departamento, p.provincia, p.nombre_completo) == ("210800", "Puno", "Melgar", "Melgar (Puno)")


def test_alto_trujillo_anio_datos_desde(ctx):
    r = texto(ctx, "Alto Trujillo")
    assert r.anio_datos_desde == 2023 and r.provisional is False


def test_sangani_provisional(ctx):
    r = texto(ctx, "Sangani")
    assert isinstance(r, Resuelto)
    assert (r.id, r.ubigeo, r.provisional) == ("120307", "120307", True)
    assert r.anio_datos_desde == 2027


@pytest.mark.parametrize("t", ["Perú", "peru", "nacional", "Todo el país", "todo el pais", "el país"])
def test_nacional_por_texto(ctx, t):
    r = texto(ctx, t)
    assert isinstance(r, Resuelto)
    assert (r.nivel, r.id) == ("nacional", "PE")


def test_nacional_por_entrada(ctx):
    r = resolver({"nacional": True}, ctx)
    assert (r.nivel, r.id, r.ubigeo) == ("nacional", "PE", None)


# ------------------------------------------------------------------ Lima y Callao (T-03)

@pytest.mark.parametrize("t,ambito,nombre", [
    ("Lima Metropolitana", "LIMA_METROPOLITANA", "Lima Metropolitana"),
    ("lima metropolitana", "LIMA_METROPOLITANA", "Lima Metropolitana"),
    ("Lima Región", "LIMA_REGION", "Lima Región (Lima Provincias)"),
    ("Lima Region", "LIMA_REGION", "Lima Región (Lima Provincias)"),
    ("Lima provincias", "LIMA_REGION", "Lima Región (Lima Provincias)"),
    ("Callao", "CALLAO", "Callao"),
    ("callao", "CALLAO", "Callao"),
    ("departamento de Callao", "CALLAO", "Callao"),
    ("Lima Metropolitana y Callao", "AREA_METROPOLITANA_LIMA_CALLAO", "Lima Metropolitana y Callao"),
])
def test_ambitos_directos(ctx, t, ambito, nombre):
    r = texto(ctx, t)
    assert isinstance(r, Resuelto), r
    assert (r.nivel, r.id, r.nombre_mostrado) == (ambito, ambito, nombre)
    assert r.ubigeo is None


def test_ambito_lima_en_distritos(ctx):
    assert texto(ctx, "San Juan de Lurigancho").ambito_lima == "LIMA_METROPOLITANA"
    assert texto(ctx, "provincia de Lima").ambito_lima == "LIMA_METROPOLITANA"
    assert texto(ctx, "Ayaviri, Yauyos").ambito_lima == "LIMA_REGION"
    assert texto(ctx, "distrito del Callao").ambito_lima == "CALLAO"
    assert texto(ctx, "Ayaviri, Melgar").ambito_lima is None


def test_lima_a_secas(ctx):
    a = texto(ctx, "Lima")
    assert isinstance(a, Aclaracion) and a.motivo == "lima_a_secas"
    assert etiquetas(a) == ["Lima Metropolitana (provincia de Lima)", "Lima Región (Lima Provincias)", "Callao"]
    assert [o["territorio"].id for o in a.opciones] == ["LIMA_METROPOLITANA", "LIMA_REGION", "CALLAO"]
    assert a.por_defecto.id == "LIMA_METROPOLITANA" and a.por_defecto.nivel == "LIMA_METROPOLITANA"
    assert a.pregunta and "Lima" in a.pregunta
    assert texto(ctx, "lima").motivo == "lima_a_secas"
    assert texto(ctx, "  LIMA ").motivo == "lima_a_secas"


# ------------------------------------------------------------------ homónimos entre niveles

def test_abancay_a_secas_aclara_entre_provincia_y_distrito(ctx):
    # X-22: el homónimo entre niveles sigue aclarando cuando ningún departamento lleva ese nombre
    a = texto(ctx, "Abancay")
    assert isinstance(a, Aclaracion) and a.motivo == "homonimo_niveles"
    assert etiquetas(a) == [
        "Abancay (provincia, departamento de Apurímac)",
        "Abancay (distrito, provincia de Abancay, departamento de Apurímac)",
    ]
    assert [o["territorio"].id for o in a.opciones] == ["030100", "030101"]
    assert a.por_defecto is None


def test_huancavelica_a_secas_se_responde_como_departamento(ctx):
    # X-22 (6/11/2026): el nombre a secas de un departamento se responde como departamento; la alternativa va en Avisos
    r = texto(ctx, "Huancavelica")
    assert isinstance(r, Resuelto) and (r.nivel, r.id) == ("departamento", "09")


@pytest.mark.parametrize("t", ["Acomayo", "Aija", "Ambo", "Andahuaylas", "abancay"])
def test_homonimos_entre_niveles(ctx, t):
    a = texto(ctx, t)
    assert isinstance(a, Aclaracion) and a.motivo == "homonimo_niveles"
    assert [o["territorio"].nivel for o in a.opciones] == ["provincia", "distrito"]
    assert len(a.opciones) >= 2


@pytest.mark.parametrize("t", ["Puno", "Cusco", "Arequipa", "Cajamarca", "huancavelica"])
def test_nombre_de_departamento_a_secas_se_resuelve_como_departamento(ctx, t):
    r = texto(ctx, t)
    assert isinstance(r, Resuelto) and r.nivel == "departamento"


def test_niveles_ordenados(ctx, monkeypatch):
    orden = {"departamento": 0, "provincia": 1, "distrito": 2}
    a = texto(ctx, "Abancay")
    niv = [orden[o["territorio"].nivel] for o in a.opciones]
    assert niv == sorted(niv)
    # con X-22 apagada (comportamiento anterior) el orden de tres niveles se conserva
    monkeypatch.setitem(_config(str(ctx.raiz)), "depto_a_secas", False)
    a = texto(ctx, "Puno")
    assert isinstance(a, Aclaracion) and a.motivo == "homonimo_niveles"
    niv = [orden[o["territorio"].nivel] for o in a.opciones]
    assert niv == sorted(niv) and niv[0] == 0


def test_palabra_de_nivel_deshace_el_empate(ctx):
    assert texto(ctx, "provincia Huancavelica").nivel == "provincia"
    assert texto(ctx, "dpto. Huancavelica").nivel == "departamento"
    assert texto(ctx, "prov de Huancavelica").nivel == "provincia"
    assert texto(ctx, "dist Huancavelica").nivel == "distrito"


# ------------------------------------------------------------------ homónimos del mismo nivel

def test_ayaviri_a_secas(ctx):
    a = texto(ctx, "Ayaviri")
    assert isinstance(a, Aclaracion) and a.motivo == "homonimo_mismo_nivel"
    assert etiquetas(a) == [
        "Ayaviri (distrito, provincia de Yauyos, departamento de Lima)",
        "Ayaviri (distrito, provincia de Melgar, departamento de Puno)",
    ]
    assert [o["territorio"].id for o in a.opciones] == ["151004", "210801"]
    assert a.por_defecto is None


def test_independencia_a_secas(ctx):
    a = texto(ctx, "Independencia")
    assert isinstance(a, Aclaracion) and a.motivo == "homonimo_mismo_nivel"
    assert [o["territorio"].id for o in a.opciones] == ["020105", "051106", "110504", "150112"]
    assert etiquetas(a)[0] == "Independencia (distrito, provincia de Huaraz, departamento de Áncash)"
    assert etiquetas(a)[3] == "Independencia (distrito, provincia de Lima, departamento de Lima)"
    assert all(e.startswith("Independencia (distrito, provincia de ") and ", departamento de " in e
               for e in etiquetas(a))


def test_san_juan_cuatro_distritos(ctx):
    a = texto(ctx, "San Juan")
    assert isinstance(a, Aclaracion) and a.motivo == "homonimo_mismo_nivel"
    assert sorted(o["territorio"].id for o in a.opciones) == ["021909", "050616", "060112", "090410"]


def test_santa_rosa_demasiadas_opciones(ctx):
    a = texto(ctx, "Santa Rosa")
    assert isinstance(a, Aclaracion) and a.motivo == "demasiadas_opciones"
    assert a.opciones == [] and a.por_defecto is None
    assert "provincia" in a.pregunta and "departamento" in a.pregunta and "10" in a.pregunta


def test_santa_rosa_con_provincia_en_el_mismo_departamento(ctx):
    a = texto(ctx, "Santa Rosa, Puno")
    assert isinstance(a, Aclaracion) and a.motivo == "homonimo_mismo_nivel"
    assert sorted(o["territorio"].id for o in a.opciones) == ["210504", "210808"]


def test_nunca_resuelve_homonimo_del_mismo_nivel(ctx):
    u = ctx.ubigeos
    d = u[(u.nivel == "distrito") & u.vigente_hasta.isna()]
    nombres = d.groupby("nombre_mostrado").ubigeo_inei.count()
    repetidos = list(nombres[nombres > 1].index)
    assert len(repetidos) >= 90
    for nombre in repetidos:
        for t in (nombre, sin_tildes(nombre).lower()):
            r = texto(ctx, t)
            assert isinstance(r, Aclaracion), (t, r)
            assert r.motivo in ("homonimo_mismo_nivel", "homonimo_niveles", "demasiadas_opciones")


def test_aclaracion_opciones_con_tildes_y_ubicacion(ctx):
    a = texto(ctx, "San Cristobal")
    assert isinstance(a, Aclaracion)
    for o in a.opciones:
        assert re.search(r"\(distrito, provincia de .+, departamento de .+\)$", o["etiqueta"])
    assert any(e.startswith("San Cristóbal (") for e in etiquetas(a))


def test_aclaracion_a_dict(ctx):
    d = texto(ctx, "Ayaviri").a_dict()
    assert d["motivo"] == "homonimo_mismo_nivel" and d["por_defecto"] is None
    assert d["opciones"][1]["territorio"]["id"] == "210801"
    assert d["opciones"][1]["etiqueta"].startswith("Ayaviri (distrito")
    json.dumps(d)
    assert texto(ctx, "Lima").a_dict()["por_defecto"]["id"] == "LIMA_METROPOLITANA"


# ------------------------------------------------------------------ coincidencia parcial

def test_albarracin(ctx):
    a = texto(ctx, "Albarracin")
    assert isinstance(a, Aclaracion) and a.motivo == "coincidencia_parcial"
    assert "Coronel Gregorio Albarracín Lanchipa (distrito, provincia de Tacna, departamento de Tacna)" in etiquetas(a)
    assert [o["territorio"].id for o in a.opciones if o["territorio"].nombre_mostrado.startswith("Coronel")] == ["230110"]
    assert "Quisiste decir" in a.pregunta


def test_toledo_por_alterno(ctx):
    a = texto(ctx, "Toledo")
    assert isinstance(a, Aclaracion) and a.motivo == "coincidencia_parcial"
    assert "060506" in [o["territorio"].id for o in a.opciones]
    assert any(e.startswith("Santa Cruz de Toled (distrito, provincia de ") for e in etiquetas(a))


def test_santa_cruz_de_toledo_completo(ctx):
    r = texto(ctx, "Santa Cruz de Toledo")
    assert isinstance(r, Resuelto) and r.id == "060506" and r.nombre_mostrado == "Santa Cruz de Toled"


@pytest.mark.parametrize("t,esperado", [("Gregorio", "230110"), ("Gregorio Albarracin", "230110"),
                                        ("Lanchipa", "230110")])
def test_parcial_siempre_pregunta(ctx, t, esperado):
    a = texto(ctx, t)
    assert isinstance(a, Aclaracion) and a.motivo == "coincidencia_parcial"
    assert esperado in [o["territorio"].id for o in a.opciones]


def test_parcial_con_demasiadas_opciones(ctx):
    a = texto(ctx, "San")
    assert isinstance(a, Aclaracion) and a.motivo == "demasiadas_opciones" and a.opciones == []


# ------------------------------------------------------------------ errores de tipeo y lugares inexistentes

@pytest.mark.parametrize("t,esperado", [
    ("Huancavelika", "09"), ("Cuzco", "08"), ("Arequipaa", "04"), ("Ayacuchoo", "05"), ("Cajamarka", "06"),
    ("Trujilo", "1301"), ("Hunacavelica", "09"), ("Lambayeque", None),
])
def test_errores_de_tipeo(ctx, t, esperado):
    r = texto(ctx, t)
    if esperado is None:  # bien escrito: no es un error de tipeo
        assert isinstance(r, (Resuelto, Aclaracion))
        return
    assert isinstance(r, Aclaracion) and r.motivo == "sin_coincidencia"
    assert 1 <= len(r.opciones) <= 3
    assert any(o["territorio"].ubigeo.startswith(esperado.ljust(6, "0")[:len(esperado)])
               or o["territorio"].ubigeo[:len(esperado)] == esperado for o in r.opciones)
    assert "Quisiste decir" in r.pregunta


def test_tipeo_sugiere_con_tildes_y_ubicacion(ctx):
    a = texto(ctx, "Huancavelika")
    assert etiquetas(a)[0].startswith("Huancavelica (")
    assert len(a.opciones) == 3


@pytest.mark.parametrize("t", ["Wakanda", "xyzxyz", "Atlantida", "Gotham City", "qqqq", "12345"])
def test_lugar_inexistente(ctx, t):
    a = texto(ctx, t)
    assert isinstance(a, Aclaracion) and a.motivo == "sin_coincidencia"
    assert a.opciones == [] and a.por_defecto is None
    assert "No encontramos ese lugar" in a.pregunta


def test_sin_resultado_de_nivel_equivocado(ctx):
    a = texto(ctx, "provincia de Ayaviri")
    assert isinstance(a, Aclaracion)
    assert all(o["territorio"].nivel == "provincia" for o in a.opciones)


# ------------------------------------------------------------------ entradas ubigeo y ámbito

@pytest.mark.parametrize("ub,nivel,id_,nombre", [
    ("09", "departamento", "09", "Huancavelica"),
    ("0901", "provincia", "090100", "Huancavelica"),
    ("090101", "distrito", "090101", "Huancavelica"),
    ("210801", "distrito", "210801", "Ayaviri"),
    ("150132", "distrito", "150132", "San Juan de Lurigancho"),
    ("120307", "distrito", "120307", "Sangani"),
    ("07", "departamento", "07", "Callao"),
])
def test_entrada_ubigeo(ctx, ub, nivel, id_, nombre):
    r = resolver({"ubigeo": ub}, ctx)
    assert isinstance(r, Resuelto)
    assert (r.nivel, r.id, r.nombre_mostrado) == (nivel, id_, nombre)


@pytest.mark.parametrize("ub", ["999999", "99", "0999", "210899"])
def test_entrada_ubigeo_desconocido(ctx, ub):
    a = resolver({"ubigeo": ub}, ctx)
    assert isinstance(a, Aclaracion) and a.motivo == "sin_coincidencia" and a.opciones == []


def test_fecha_anterior_a_la_creacion_del_distrito(ctx):
    """Alto Trujillo existe desde 2022-12-16: antes de esa fecha no se resuelve; con fecha posterior, sí."""
    antes = resolver({"texto": "Alto Trujillo"}, ctx, fecha="2000-01-01")
    assert isinstance(antes, Aclaracion) and antes.motivo == "sin_coincidencia"
    despues = resolver({"texto": "Alto Trujillo"}, ctx, fecha="2025-01-01")
    assert isinstance(despues, Resuelto) and despues.id == "130112"


@pytest.mark.parametrize("amb", ["LIMA_METROPOLITANA", "LIMA_REGION", "CALLAO", "AREA_METROPOLITANA_LIMA_CALLAO"])
def test_entrada_ambito(ctx, amb):
    r = resolver({"ambito": amb}, ctx)
    assert isinstance(r, Resuelto) and (r.nivel, r.id) == (amb, amb)


def test_solo_distritos_vigentes_por_nombre(ctx):
    u = ctx.ubigeos
    vig = u[u.vigente_hasta.isna()]
    viejos = u[u.vigente_hasta.notna() & (u.nivel == "distrito")]
    assert len(viejos) > 0
    solo_viejos = sorted(set(viejos.nombre_normalizado) - set(vig.nombre_normalizado))
    vigentes = set(vig.ubigeo_inei)
    for n in solo_viejos:
        r = texto(ctx, n)
        if isinstance(r, Resuelto):
            assert r.ubigeo in vigentes
        else:
            assert all(o["territorio"].ubigeo in vigentes for o in r.opciones)


# ------------------------------------------------------------------ Q1–Q4 y nombres_mostrados.yaml

CARPETA_Q = Path(RAIZ_REAL) / "curados" / "motor" / "consultas_minimas"


@pytest.mark.parametrize("q,nivel,id_", [("q1", "departamento", "09"), ("q2", "distrito", "210801"),
                                         ("q3", "distrito", "150132"), ("q4", "nacional", "PE")])
def test_consultas_q1_q4(ctx, q, nivel, id_):
    c = json.loads((CARPETA_Q / f"{q}.json").read_text(encoding="utf-8"))
    lugar = c["territorio"].get("dentro_de", c["territorio"])
    r = resolver(lugar, ctx)
    assert isinstance(r, Resuelto)
    assert (r.nivel, r.id) == (nivel, id_)


def _ubigeos_mostrados():
    p = Path(RAIZ_REAL) / "curados" / "capa0" / "nombres_mostrados.yaml"
    return [c["ubigeo"] for c in yaml.safe_load(p.read_text(encoding="utf-8"))["correcciones"]]


def test_nombres_mostrados_son_15():
    assert len(_ubigeos_mostrados()) == 15


@pytest.mark.parametrize("ubigeo", _ubigeos_mostrados())
def test_nombres_mostrados_sin_tildes(ctx, ubigeo):
    u = ctx.ubigeos
    fila = u[(u.ubigeo_inei == ubigeo) & u.vigente_hasta.isna()].iloc[0]
    mostrado = fila.nombre_mostrado
    r = texto(ctx, sin_tildes(mostrado))
    if isinstance(r, Resuelto):
        assert r.nombre_mostrado == mostrado
    else:
        assert isinstance(r, Aclaracion)
        ops = [o for o in r.opciones if o["territorio"].ubigeo == ubigeo]
        assert ops, (mostrado, etiquetas(r))
        assert ops[0]["etiqueta"].startswith(mostrado)
        assert ops[0]["territorio"].nombre_mostrado == mostrado


def test_tildes_en_etiquetas_de_resueltos(ctx):
    assert texto(ctx, "Anguia, Chota").nombre_mostrado == "Anguía"
    assert texto(ctx, "Anguia, Chota").nombre_completo == "Anguía (Chota, Cajamarca)"
    assert texto(ctx, "Acari, Caraveli").nombre_mostrado == "Acarí"


# ------------------------------------------------------------------ entradas inválidas / Resuelto es consistente

def test_a_dict_serializable(ctx):
    for t in ("Ayaviri, Melgar", "Lima Metropolitana", "Perú", "Sangani"):
        d = texto(ctx, t).a_dict()
        json.dumps(d)
        assert set(d) >= {"nivel", "id", "ubigeo", "nombre_mostrado", "nombre_completo", "departamento",
                          "provincia", "ambito_lima", "anio_datos_desde", "provisional"}


def test_resolver_es_determinista(ctx):
    a = texto(ctx, "Independencia").a_dict()
    assert a == texto(ctx, "Independencia").a_dict()


def test_entrada_sin_forma_conocida(ctx):
    a = resolver({}, ctx)
    assert isinstance(a, Aclaracion) and a.motivo == "sin_coincidencia"
