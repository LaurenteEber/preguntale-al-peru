"""Los planes de las 3 recetas de la fase 0 (M0-07). Los archivos YAML de las recetas son de M0-10: aquí se arman a mano,
con los mismos predicados que `curados/inferencia/universos_analiticos.yaml` (anemia con HC57 y con HC57A; DCI con HC70)."""
from pap.inferencia.plan import Plan

NIVELES = ("nacional", "dominio_subnacional", "departamento", "CALLAO", "LIMA_METROPOLITANA", "LIMA_REGION")


def _v(archivo: str, variable: str) -> str:
    return f"ENDES·2024·{archivo}·{variable}"


def plan_anemia(nivel: str = "nacional", id_: str | None = None, cortes: tuple[str, ...] = ()) -> Plan:
    """Anemia 6–35 meses, criterio anterior: HC57 en {1,2,3} (grave, moderada, leve) sobre HC1 6–35 y HC57 en 1–4."""
    return Plan.model_validate({
        "origen": "receta", "receta_id": "endes_anemia_6_35m", "encuesta": "ENDES", "anios": [2024], "unidad": "nino",
        "medida": "proporcion",
        "indicador": {"combinar": "una", "condiciones": [{"var": _v("RECH6", "HC57"), "op": "en", "valores": [1, 2, 3]}]},
        "universo": {"restricciones": [{"var": _v("RECH6", "HC1"), "op": "entre", "valores": [6, 35]},
                                       {"var": _v("RECH6", "HC57"), "op": "en", "valores": [1, 2, 3, 4]}]},
        "cortes": list(cortes), "territorio": {"nivel": nivel, "id": id_}})


def plan_anemia_oms2024(nivel: str = "nacional", id_: str | None = None, cortes: tuple[str, ...] = ()) -> Plan:
    """Anemia 6–35 meses, directriz OMS 2024: lo mismo con HC57A."""
    return Plan.model_validate({
        "origen": "receta", "receta_id": "endes_anemia_6_35m_oms2024", "encuesta": "ENDES", "anios": [2024], "unidad": "nino",
        "medida": "proporcion",
        "indicador": {"combinar": "una", "condiciones": [{"var": _v("RECH6", "HC57A"), "op": "en", "valores": [1, 2, 3]}]},
        "universo": {"restricciones": [{"var": _v("RECH6", "HC1"), "op": "entre", "valores": [6, 35]},
                                       {"var": _v("RECH6", "HC57A"), "op": "en", "valores": [1, 2, 3, 4]}]},
        "cortes": list(cortes), "territorio": {"nivel": nivel, "id": id_}})


def plan_dci(nivel: str = "nacional", id_: str | None = None, cortes: tuple[str, ...] = ()) -> Plan:
    """Desnutrición crónica de 0 a 59 meses: HC70 < −200 (menos de 2 DE) entre quienes tienen HC70 válido (−9989 a 9989)."""
    return Plan.model_validate({
        "origen": "receta", "receta_id": "endes_dci_menores_5", "encuesta": "ENDES", "anios": [2024], "unidad": "nino",
        "medida": "proporcion",
        "indicador": {"combinar": "una", "condiciones": [{"var": _v("RECH6", "HC70"), "op": "<", "valores": [-200]}]},
        "universo": {"restricciones": [{"var": _v("RECH6", "HC1"), "op": "entre", "valores": [0, 59]},
                                       {"var": _v("RECH6", "HC70"), "op": "entre", "valores": [-9989, 9989]}]},
        "cortes": list(cortes), "territorio": {"nivel": nivel, "id": id_}})


RECETAS = {"anemia": plan_anemia, "anemia_oms2024": plan_anemia_oms2024, "dci": plan_dci}
