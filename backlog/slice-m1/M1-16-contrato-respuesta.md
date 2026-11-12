# M1-16 — Contrato v2 y respuesta

**Se deriva de** el diseño §19 y de la decisión del dueño del 10/11/2026 (niveles 1 y 2 con varias fuentes).

## Cambio al diseño (se registra con su motivo)

El contrato v2 nace con **partes por fuente,** para que más adelante una respuesta pueda juntar lo que aporta cada encuesta sin romper el contrato. En M1 siempre hay **una** parte.

```json
{
  "version_contrato": 2,
  "tipo": "respuesta",
  "entendimos": "…",
  "partes": [
    {
      "fuente": {"id": "INEI-ENDES", "nombre": "ENDES", "anio": 2024, "tipo_fuente": "muestra"},
      "papel": "resultado",
      "sustitucion": null,
      "sello": {"clase": "oficial_inei", "texto": "…"},
      "universo_corto": "…",
      "pregunta_encuesta": null,
      "cifra_clave": {"marcador": "c:…"},
      "cifra_clave_grupos": [],
      "prueba_grupos": null,
      "confianza": {"nivel": "alta", "motivo": "…"},
      "plan": {"palabras": ["…"], "tecnico": {}},
      "huella_datos": ["…"],
      "id_plan": "sha256…"
    }
  ],
  "capas": {"1": "…", "2": "…", "3": "…"},
  "opciones": [],
  "alternativas": []
}
```

- Lo que antes iba suelto en el §19.2 (`sello`, `universo_corto`, `pregunta_encuesta`, `cifra_clave`, `cifra_clave_grupos`, `prueba_grupos`, `confianza`, `plan`, `huella_datos`, `id_plan`, `sustitucion`) va **dentro de cada parte.**
- `aclaracion`, `no_se_puede`, `indeterminado` y `mensaje` llevan `partes: []`; sus opciones y alternativas van arriba, cada una con su `id_plan`.
- `entendimos`, `capas`, `opciones` y `alternativas` siguen arriba.
- Actualizar el §19.2 de `docs/diseno/motor_inferencia.md` y `docs/especificaciones/contrato_respuesta.md` con este esquema y su motivo; registrar el cambio en `decisiones.md` (fila R-04).

## Tareas

1. **Esquema** del contrato v2 en `src/pap/esquemas/`, con `tipo` ∈ {`respuesta`, `aclaracion`, `no_se_puede`, `indeterminado`, `mensaje`}.
2. **Respuesta** (`inferencia/respuesta.py`, reutilizando `motor/capas.py` y el validador):
   - bloques que nunca se pliegan y no cuentan para las 125 palabras: `entendimos`, `sustitucion`, `universo_corto`, `pregunta_encuesta` y `sello`;
   - capa 1: respuesta corta, cifra clave (o por grupos, hasta 3 en lista vertical), «Ojo al leer», confianza y hasta 2 botones;
   - capa 2: contexto, comparaciones, tasa de no respuesta y tercera alternativa;
   - capa 3: el plan en palabras; el JSON del plan detrás de «Ver el plan técnico».
3. **«No puedo» e `indeterminado`:** textos del §19.1.
4. **Validador y corrector** actuales sobre todos los textos; los números entran solo por marcadores (R-04).
5. **Compatibilidad:** la web actual no se rompe. Los campos nuevos son opcionales para ella y el contrato v1 sigue saliendo del motor actual.

## Criterios de aceptación

- [ ] Q1–Q4 por las recetas producen un contrato v2 válido, con una parte.
- [ ] El peor caso de la capa 1 medido: no pasa de 125 palabras.
- [ ] Las pruebas de la web y de la API del slice 3 siguen en verde sin regrabar.
- [ ] Una respuesta de prueba con dos partes (construida a mano) valida contra el esquema.

## Fuera

Mostrar el contrato v2 en la web (M4). El orquestador que produce varias partes (después de M3).
