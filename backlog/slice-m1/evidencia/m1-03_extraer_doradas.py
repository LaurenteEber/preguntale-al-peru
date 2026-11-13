#!/usr/bin/env python3
"""M1-03, tarea 4: copia de las doradas por corte desde el PDF del INEI a `curados/inferencia/doradas_cortes.csv`.

Cada cifra sale de la columna «Valor estimado 2024» y cada caso de «Número de casos sin ponderar» de la fila del cuadro, leída con
`pdftotext -layout` de la hoja indicada. Nada se escribe a mano. Si una fila falta o trae el valor entre paréntesis (referencial),
el script se detiene.

Uso (desde la raíz del repositorio):
    python3 -I backlog/slice-m1/evidencia/m1-03_extraer_doradas.py <ruta del PDF en el almacén> <csv de salida>
El PDF es el recurso `endes-2024-informe-ppr` (biblioteca/cruda/capturas/INEI-ENDES/2026-11-12-5/datapackage.json: `path`)."""
import csv
import re
import subprocess
import sys
from pathlib import Path

INFORME = ("INEI, «Perú: Indicadores de Resultados de los Programas Presupuestales, 2024. ENDES» (recurso endes-2024-informe-ppr)")
REGION = [("Costa", "Costa"), ("Sierra", "Sierra"), ("Selva", "Selva")]
QUINTIL = [("Quintil inferior", "los más pobres"), ("Segundo quintil", "pobre"), ("Quintil intermedio", "medio"),
           ("Cuarto quintil", "rico"), ("Quintil superior", "más rico")]
EDAD_ANEMIA = [(x, x) for x in ("6 a 8 meses", "9 a 11 meses", "12 a 17 meses", "18 a 23 meses", "24 a 35 meses")]
EDAD_DCI = [("Menores de 36 meses", "Menores de 36 meses"), ("De 36 a 59 meses", "De 36 a 59 meses")]
# (cuadro, corte, filas, sigla del id)
BLOQUES = [("04", "region_natural", REGION, "REGION"), ("04", "quintil_riqueza", QUINTIL, "QUINTIL"), ("04", "grupo_edad", EDAD_DCI, "EDAD"),
           ("06", "region_natural", REGION, "REGION"), ("06", "quintil_riqueza", QUINTIL, "QUINTIL"), ("06B", "grupo_edad", EDAD_ANEMIA, "EDAD"),
           ("6.1", "region_natural", REGION, "REGION"), ("6.1", "quintil_riqueza", QUINTIL, "QUINTIL"), ("6.1B", "grupo_edad", EDAD_ANEMIA, "EDAD")]
HOJA = {"04": (51, 49), "06": (55, 53), "06B": (57, 55), "6.1": (58, 56), "6.1B": (60, 58)}
RECETA = {"04": ("endes_dci_menores_5", "DCI"), "06": ("endes_anemia_6_35m", "ANE"), "06B": ("endes_anemia_6_35m", "ANE"),
          "6.1": ("endes_anemia_6_35m_oms2024", "ANEOMS"), "6.1B": ("endes_anemia_6_35m_oms2024", "ANEOMS")}
TOTAL = {"04": ("12.1", "19,511"), "06": ("43.7", "9,959"), "06B": ("43.7", "9,959"), "6.1": ("35.3", "9,959"), "6.1B": ("35.3", "9,959")}
NUM = re.compile(r"\(?-?[\d.,]+\)?")


def fila(texto: str, etiqueta: str) -> list[str]:
    """Los números de la fila cuya etiqueta es exactamente `etiqueta` (no «Costa urbana» cuando se busca «Costa»)."""
    for linea in texto.splitlines():
        m = re.match(rf"^\s*{re.escape(etiqueta)}\s+(\(?-?\d.*)$", linea)
        if m:
            return NUM.findall(m.group(1))
    raise SystemExit(f"no encuentro la fila «{etiqueta}»")


def main(pdf: str, salida: str) -> None:
    textos = {c: subprocess.run(["pdftotext", "-layout", "-f", str(h), "-l", str(h), pdf, "-"], capture_output=True, text=True, check=True).stdout
              for c, (h, _) in HOJA.items()}
    filas = []
    for cuadro, corte, etiquetas, sigla in BLOQUES:
        receta, pref = RECETA[cuadro]
        hoja, pagina = HOJA[cuadro]
        total = fila(textos[cuadro], "Total")
        if (total[5], total[9]) != TOTAL[cuadro]:
            raise SystemExit(f"Cuadro {cuadro}: el total no es el esperado: {total[5]} / {total[9]}")
        for i, (etiqueta, categoria) in enumerate(etiquetas, start=1):
            n = fila(textos[cuadro], etiqueta)
            valor, casos = n[5], n[9]
            if valor.startswith("(") or "," in valor:
                raise SystemExit(f"Cuadro {cuadro}, «{etiqueta}»: el valor 2024 {valor} es referencial o no decimal; revisar a mano")
            filas.append({
                "id_cifra": f"DOR-{pref}-2024-PE-{sigla}-{i}", "receta_id": receta, "anio": 2024, "nivel": "nacional", "territorio": "PE",
                "corte": corte, "categoria": categoria, "valor_publicado": valor, "decimales": 1, "casos_publicados": casos.replace(",", ""),
                "cita": f"{INFORME}, Cuadro N.º {cuadro} p. {pagina} (PDF {hoja}), fila «{etiqueta}», columnas «Valor estimado 2024» y "
                        f"«Número de casos sin ponderar»"})
    with open(salida, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, ["id_cifra", "receta_id", "anio", "nivel", "territorio", "corte", "categoria", "valor_publicado", "decimales",
                               "casos_publicados", "cita"])
        w.writeheader()
        w.writerows(filas)
    print(f"{len(filas)} filas en {salida}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    main(sys.argv[1], sys.argv[2])
