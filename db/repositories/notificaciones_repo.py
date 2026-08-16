from db.connection import DBConnection


class NotificacionesRepository:
    """Solo CRUD sobre `notificaciones_whatsapp` — nunca hace commit ni
    rollback (eso lo maneja el servicio, ver AGENTS.md)."""

    def __init__(self, db: DBConnection):
        self.db = db

    def create(self, socio_id, numero_e164, texto, documento_tipo, documento_id, detalle, estado="pendiente"):
        """Encola una notificación de WhatsApp en la misma tabla que usa la API
        de bgc-platform (`notificaciones_whatsapp`, ver ADR-010). El bot, que
        corre en Railway y sondea esa tabla cada 60 segundos, la recoge, genera
        el PDF llamando a la API, y lo manda por WhatsApp — este software nunca
        habla directamente con Meta, solo encola."""
        cursor = self.db.conn.cursor()
        cursor.execute("""
            INSERT INTO notificaciones_whatsapp
                (socio_id, numero_e164, texto, documento_tipo, documento_id, detalle, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (socio_id, numero_e164, texto, documento_tipo, documento_id, detalle, estado))
        return cursor.fetchone()["id"]
