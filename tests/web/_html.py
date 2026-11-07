"""Un árbol mínimo sobre `html.parser` (sin dependencias nuevas) para leer las páginas de la web en las pruebas."""
from __future__ import annotations

from html.parser import HTMLParser

VACIOS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
SIN_TEXTO = {"script", "style"}


class Nodo:
    def __init__(self, tag: str, attrs: dict, padre: "Nodo | None" = None):
        self.tag, self.attrs, self.padre, self.hijos = tag, attrs, padre, []

    def __repr__(self) -> str:
        return f"<{self.tag} {self.attrs}>"

    def recorrer(self):
        yield self
        for h in self.hijos:
            if isinstance(h, Nodo):
                yield from h.recorrer()

    def buscar(self, tag: str | None = None, **attrs) -> list["Nodo"]:
        """Nodos con ese tag y esos atributos; `True` pide solo que el atributo exista."""
        return [n for n in self.recorrer() if (tag is None or n.tag == tag)
                and all((k.rstrip("_") in n.attrs) if v is True else n.attrs.get(k.rstrip("_").replace("__", "-")) == v
                        for k, v in attrs.items())]

    def texto(self, sin_eco: bool = False) -> str:
        """Texto de todos los nodos (los `<details>` cerrados incluidos), sin script ni style ni atributos."""
        if self.tag in SIN_TEXTO or (sin_eco and "data-eco" in self.attrs):
            return ""
        return "".join(h if isinstance(h, str) else h.texto(sin_eco) for h in self.hijos)

    def tiene_clase(self, c: str) -> bool:
        return c in (self.attrs.get("class") or "").split()


class _Constructor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.raiz = Nodo("#raiz", {})
        self.actual = self.raiz

    def handle_starttag(self, tag, attrs):
        n = Nodo(tag, {k: (v if v is not None else "") for k, v in attrs}, self.actual)
        self.actual.hijos.append(n)
        if tag not in VACIOS:
            self.actual = n

    def handle_endtag(self, tag):
        n = self.actual
        while n is not self.raiz and n.tag != tag:
            n = n.padre
        if n is not self.raiz:
            self.actual = n.padre

    def handle_data(self, data):
        self.actual.hijos.append(data)


def leer(html: str) -> Nodo:
    c = _Constructor()
    c.feed(html)
    return c.raiz


def formulario(nodo_form: Nodo, boton: dict | None = None) -> dict:
    """Los campos que enviaría un navegador sin JavaScript: los `input`, `textarea` y el botón pulsado."""
    datos = {}
    for n in nodo_form.recorrer():
        if n.tag == "input" and n.attrs.get("name") and n.attrs.get("type", "text") != "submit":
            datos[n.attrs["name"]] = n.attrs.get("value", "")
        elif n.tag == "textarea" and n.attrs.get("name"):
            datos[n.attrs["name"]] = n.texto()
    if boton:
        datos.update(boton)
    return datos
