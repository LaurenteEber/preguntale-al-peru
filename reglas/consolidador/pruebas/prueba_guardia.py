"""Prueba negativa de la guardia de CAMPOS_REGLAS (consolida_reglas.py). No modifica nada: copia reglas/ y catalogo/
a un directorio temporal, agrega al final de ajustes_dueno.py una sobrescritura (regla, campo, 'PISADO') y regenera.
Casos 'falla': el campo ya lo corrigió una capa anterior → el consolidador debe abortar con «pisa un campo corregido».
Casos 'pasa': campo intacto o solo renombrado mecánicamente → debe regenerar sin error.
Uso: python3 reglas/consolidador/pruebas/prueba_guardia.py   (desde la raíz del repositorio o de una copia)"""
import os, shutil, subprocess, sys, tempfile
H = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # reglas/
RAIZ = os.path.dirname(H)
CASOS = [  # (regla, campo, capa que lo tocó antes, resultado esperado)
 ('R-TERRITORIO-08', 'condicion', 'AGREGADOS_REGLAS_R3 (excepción SIEN, ronda 4)', 'falla'),
 ('R-GASTO-01', 'condicion', 'AGREGADOS_REGLAS (auditoría Ola 0) y PARCHES_REGLAS_R3 (M1)', 'falla'),
 ('R-TERRITORIO-05', 'implementacion', 'PARCHES_REGLAS (S1) y AGREGADOS_REGLAS', 'falla'),
 ('R-REG-07', 'implementacion', 'PARCHES_REGLAS_R3 (ronda 3)', 'falla'),
 ('R-REG-05', 'condicion', 'CA.POST_RENOMBRE', 'falla'),
 ('R-EST-01', 'casos_borde', 'CP replace sobre la regla entera (PR-26)', 'falla'),
 ('R-GASTO-07', 'casos_borde', 'CP replace sobre la regla entera (PR-29)', 'falla'),
 ('R-GASTO-02', 'casos_borde', 'CP borde (PR-17)', 'falla'),
 ('R-EST-01', 'condicion', 'CA.PARCHES', 'falla'),
 ('R-REG-12', 'condicion', 'PARCHES_V2/V3/V4', 'falla'),
 ('R-REG-12', 'parametros', 'PARCHES_V3/V4 (ruta padre de lo corregido)', 'falla'),
 ('R-ENC-07', 'implementacion', 'solo CA.RENOMBRES (mecánico)', 'pasa'),
 ('R-ENC-01', 'ejemplo', 'ninguna', 'pasa'),
]
def corre(rid, campo):
    with tempfile.TemporaryDirectory() as t:
        shutil.copytree(H, os.path.join(t, 'reglas')); shutil.copytree(os.path.join(RAIZ, 'catalogo'), os.path.join(t, 'catalogo'))
        with open(os.path.join(t, 'reglas', 'consolidador', 'ajustes_dueno.py'), 'a') as f:
            f.write(f"\nCAMPOS_REGLAS += [({rid!r}, {campo!r}, 'PISADO')]\n")
        p = subprocess.run([sys.executable, os.path.join(t, 'reglas', 'consolidador', 'consolida_reglas.py')], capture_output=True, text=True)
        if p.returncode == 0: return 'pasa'
        return 'falla' if 'pisa un campo corregido' in p.stderr else 'error: ' + p.stderr.strip().splitlines()[-1][:160]
mal = 0
for rid, campo, capa, esperado in CASOS:
    r = corre(rid, campo); ok = r == esperado; mal += not ok
    print(f"{'OK ' if ok else 'MAL'} {rid}.{campo:<15} esperado={esperado:<5} obtenido={r:<5} ({capa})")
print('fallos:', mal); sys.exit(1 if mal else 0)
