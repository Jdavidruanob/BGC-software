"""Encola el envío de un recibo o una liquidación por WhatsApp desde el
software de escritorio, reusando exactamente el mismo mecanismo que usa la
API cuando el tesorero opera por Telegram (ver ADR-010/ADR-011 en
bgc-platform): inserta una fila en `notificaciones_whatsapp`, y el bot (que
corre en Railway y sondea esa tabla cada 60 segundos) la recoge, genera el
PDF llamando a la API, y lo manda por WhatsApp. Este software nunca habla
directamente con Meta; solo encola.

A diferencia de las notificaciones automáticas que dispara la API (que se
crean como 'borrador' y esperan la aprobación del tesorero en el chat de
Telegram), esta cola nace directamente en 'pendiente': el clic derecho en el
libro auxiliar ES la confirmación del tesorero.
"""

from db.repositories.notificaciones_repo import NotificacionesRepository
from utils.telefono import derivar_whatsapp_e164

_CIERRE = "¡Que tengas un excelente día!"
# Misma palabra genérica que usa notificaciones_wire.py en la API, para que el
# mensaje se lea igual sin importar desde dónde se encoló.
_DOCUMENTO_POR_TIPO = {"recibo": "recibo", "liquidacion": "liquidación"}


class NotificacionWhatsappService:
    def __init__(self, db):
        self._db = db
        self._repo = NotificacionesRepository(db)

    def enviar_recibo(self, recibo_id: int) -> str:
        """Encola el recibo #`recibo_id` para el socio que aparece como
        'Recibí de' (el único que se notifica, igual que `notificar_recibo`
        en la API). Retorna su nombre completo. Lanza ValueError si el recibo
        no existe o el socio no tiene WhatsApp registrado."""
        cursor = self._db.conn.cursor()
        try:
            cursor.execute("SELECT socio_id FROM recibos WHERE id = %s", (recibo_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"El recibo #{recibo_id} ya no existe.")
            socio_nombre = self._encolar(cursor, row["socio_id"], "recibo", recibo_id)
            self._db.conn.commit()
            return socio_nombre
        except Exception:
            self._db.conn.rollback()
            raise

    def enviar_liquidacion(self, letra_id: int) -> list[str]:
        """Encola la liquidación de la letra `letra_id` para cada socio del
        crédito (un crédito puede tener varios). Retorna los nombres a los
        que sí se pudo encolar. Lanza ValueError si la letra no existe o
        ninguno de sus socios tiene WhatsApp registrado."""
        cursor = self._db.conn.cursor()
        try:
            cursor.execute("SELECT socio_id FROM socio_credito WHERE credito_letra = %s", (letra_id,))
            socio_ids = [r["socio_id"] for r in cursor.fetchall()]
            if not socio_ids:
                raise ValueError(f"La letra #{letra_id} no tiene socios asociados.")

            enviados = []
            for socio_id in socio_ids:
                try:
                    enviados.append(self._encolar(cursor, socio_id, "liquidacion", letra_id))
                except ValueError:
                    continue  # ese socio en particular no tiene número; se sigue con el resto
            if not enviados:
                raise ValueError(
                    "Ninguno de los socios de esta letra tiene un número de WhatsApp válido registrado."
                )
            self._db.conn.commit()
            return enviados
        except Exception:
            self._db.conn.rollback()
            raise

    def _encolar(self, cursor, socio_id: int, documento_tipo: str, documento_id: int) -> str:
        cursor.execute(
            "SELECT nombres, apellidos, celular, whatsapp_e164 FROM socios WHERE id = %s",
            (socio_id,),
        )
        socio = cursor.fetchone()
        if not socio:
            raise ValueError(f"El socio #{socio_id} ya no existe.")

        numero = derivar_whatsapp_e164(socio.get("whatsapp_e164"), socio.get("celular"))
        if numero is None:
            raise ValueError(
                f"{socio['nombres']} {socio['apellidos']} no tiene un número de WhatsApp válido registrado."
            )

        documento = _DOCUMENTO_POR_TIPO[documento_tipo]
        partes = (socio["nombres"] or "").strip().split()
        primer_nombre = partes[0].capitalize() if partes else ""
        saludo = f"Hola {primer_nombre} 👋" if primer_nombre else "Hola 👋"
        texto = f"{saludo}\n\nAqui tienes tu {documento}.\n\n{_CIERRE}"

        self._repo.create(socio_id, numero, texto, documento_tipo, documento_id, documento, estado="pendiente")
        return f"{socio['nombres']} {socio['apellidos']}"
