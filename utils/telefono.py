"""Deriva el número de WhatsApp de un socio a partir de `whatsapp_e164` o
`celular`. Réplica de `coop_core.utils.telefono.derivar_whatsapp_e164` de
bgc-platform (ese paquete no es una dependencia de este repo, que solo tiene
acceso directo a la misma base de datos) — si la regla cambia allá, hay que
cambiarla acá también.

La mayoría de socios solo tienen `celular` cargado (el dato histórico de este
software); `whatsapp_e164` es el campo explícito para cuando se confirme el
número por WhatsApp. Mientras tanto, se deriva de `celular` si tiene la forma
de un celular colombiano (10 dígitos, empieza en 3).
"""


def derivar_whatsapp_e164(whatsapp_e164, celular):
    if whatsapp_e164:
        return whatsapp_e164
    if not celular:
        return None
    digitos = "".join(c for c in celular if c.isdigit())
    if len(digitos) == 10 and digitos.startswith("3"):
        return f"+57{digitos}"
    return None
