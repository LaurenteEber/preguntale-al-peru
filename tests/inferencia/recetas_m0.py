"""Los planes de las 3 recetas de la fase 0. Las definiciones viven en `curados/inferencia/recetas/*.yaml` (M0-10): estos helpers
solo las leen (`pap.inferencia.recetas.leer_receta`), así que hay una sola fuente. A diferencia de `Receta.a_plan`, aceptan cualquier
corte (las pruebas del verificador necesitan cortes pendientes o inexistentes para ver que los rechaza)."""
from pap.inferencia.plan import Plan
from pap.inferencia.recetas import leer_receta

from conftest import RAIZ_REAL

NIVELES = ("nacional", "dominio_subnacional", "departamento", "CALLAO", "LIMA_METROPOLITANA", "LIMA_REGION")


def _plan(receta_id: str, nivel: str, id_: str | None, cortes: tuple[str, ...]) -> Plan:
    plan = leer_receta(RAIZ_REAL, receta_id).a_plan(2024, nivel, id_)
    return Plan.model_validate({**plan.model_dump(mode="json"), "cortes": list(cortes)})


def plan_anemia(nivel: str = "nacional", id_: str | None = None, cortes: tuple[str, ...] = ()) -> Plan:
    """Anemia 6–35 meses, criterio anterior: HC57 en {1,2,3} (grave, moderada, leve) sobre HC1 6–35 y HC57 en 1–4."""
    return _plan("endes_anemia_6_35m", nivel, id_, cortes)


def plan_anemia_oms2024(nivel: str = "nacional", id_: str | None = None, cortes: tuple[str, ...] = ()) -> Plan:
    """Anemia 6–35 meses, directriz OMS 2024: lo mismo con HC57A."""
    return _plan("endes_anemia_6_35m_oms2024", nivel, id_, cortes)


def plan_dci(nivel: str = "nacional", id_: str | None = None, cortes: tuple[str, ...] = ()) -> Plan:
    """Desnutrición crónica de 0 a 59 meses: HC70 < −200 (menos de 2 DE) entre quienes tienen HC70 válido (−9989 a 9989)."""
    return _plan("endes_dci_menores_5", nivel, id_, cortes)


RECETAS = {"anemia": plan_anemia, "anemia_oms2024": plan_anemia_oms2024, "dci": plan_dci}
