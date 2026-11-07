/* S3-04 — «Buscando…»: único JavaScript. La página funciona igual sin él; el texto sale del atributo data-buscando. */
document.addEventListener("submit", function (ev) {
  var form = ev.target;
  var botones = form.querySelectorAll("button[type=submit]");
  var pulsado = ev.submitter || botones[0];
  /* Se espera un instante: un botón desactivado antes de enviar no manda su `name` (el número de la aclaración). */
  setTimeout(function () {
    for (var i = 0; i < botones.length; i++) { botones[i].disabled = true; }
    if (pulsado && pulsado.dataset.buscando) { pulsado.textContent = pulsado.dataset.buscando; }
  }, 0);
});
