# M1-15 — Contraste oficial, sellos y confianza

**Se deriva de** el diseño §15.2 y §18.

## Tareas

1. **«Coincide»** solo si el plan es la receta de esa cifra oficial o tiene su misma `huella_uy`, y el valor está dentro de E-05.
2. **Cifra oficial del mismo tema con otra definición:** no se dice «difiere en X puntos»; se dice que el INEI publica otra definición y qué cambia.
3. **Sellos** (cuatro, §18) en `curados/motor/textos/capas.yaml`.
4. **Confianza** según el §15.2: alta, media o baja, con su motivo en palabras sencillas. Con las recetas ya en `verificado`, desaparece el supuesto `confianza_receta_no_verificada`.
5. **Intervalo visible:** el del INEI cuando existe; si no, el propio (E-04).

## Criterios de aceptación

- [ ] Las recetas en un dominio con dorada salen con «Cifra oficial del INEI» y confianza alta.
- [ ] Una receta en un corte sin cifra oficial sale con el segundo sello y confianza media.
- [ ] Un plan compuesto sale con su sello y nunca dice «coincide».
