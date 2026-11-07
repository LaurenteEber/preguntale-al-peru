/* S3-04 — «Buscando…»: único JavaScript. La página funciona igual sin él; el texto sale del atributo data-buscando. */
document.addEventListener("submit", function (ev) {
  var form = ev.target;
  var botones = form.querySelectorAll("button[type=submit]");
  var pulsado = ev.submitter || botones[0];
  /* Se espera un instante: un botón desactivado antes de enviar no manda su `name` (el número de la aclaración). */
  setTimeout(function () {
    for (var i = 0; i < botones.length; i++) { botones[i].disabled = true; }
    if (pulsado && pulsado.dataset.buscando) { pulsado.dataset.etiqueta = pulsado.textContent; pulsado.textContent = pulsado.dataset.buscando; }
  }, 0);
});
/* S3-11: al volver atrás, el navegador puede mostrar la página guardada (bfcache) con los botones aún en «Buscando…». */
window.addEventListener("pageshow", function (ev) {
  if (!ev.persisted) { return; }
  var botones = document.querySelectorAll("button[type=submit]");
  for (var i = 0; i < botones.length; i++) {
    botones[i].disabled = false;
    if (botones[i].dataset.etiqueta) { botones[i].textContent = botones[i].dataset.etiqueta; delete botones[i].dataset.etiqueta; }
  }
});
