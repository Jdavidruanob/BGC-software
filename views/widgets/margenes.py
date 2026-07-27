"""Márgenes laterales que se encogen cuando la ventana es angosta.

Las páginas usan márgenes laterales generosos (80 px) que se ven bien en un
monitor grande, pero que en pantallas pequeñas —o con el escalado de Windows
al 125 % o 150 %, que reduce el espacio real disponible— son 160 px que la
ventana exige sin dar nada a cambio, y la empujan a ser más ancha que el
monitor.

Con esto los márgenes se mantienen mientras haya sitio y se reducen cuando no
lo hay, así que el aspecto en pantalla grande no cambia y en pantalla chica la
ventana cabe.
"""

MARGEN_AMPLIO = 80
MARGEN_ESTRECHO = 24
# Por debajo de este ancho se considera que la ventana está apretada.
UMBRAL = 1100


def margen_lateral(ancho: int) -> int:
    """Margen lateral que corresponde a un ancho de ventana dado."""
    return MARGEN_AMPLIO if ancho >= UMBRAL else MARGEN_ESTRECHO


def aplicar_margenes_adaptativos(widget, ancho: int) -> None:
    """Ajusta los márgenes laterales del layout de `widget` según el ancho.

    Conserva los márgenes de arriba y abajo. No hace nada si el widget aún no
    tiene layout. Llamar desde `resizeEvent`.
    """
    layout = widget.layout()
    if layout is None:
        return
    m = layout.contentsMargins()
    lateral = margen_lateral(ancho)
    if m.left() == lateral and m.right() == lateral:
        return  # ya está como debe: evita relayouts innecesarios
    layout.setContentsMargins(lateral, m.top(), lateral, m.bottom())
