"""
Fachada de compatibilidad. Delega a los repositorios del paquete db/.
Los servicios usan repos directamente (inyectados desde app.py via las propiedades
db_conn, config_repo, auxiliar_repo, etc.). Esta fachada permanece solo para
las vistas de solo lectura y el wiring en app.py.
"""
from db.connection import DBConnection
from db.schema import SchemaManager
from db.migration import MigrationService
from db.repositories.socios_repo import SociosRepository
from db.repositories.creditos_repo import CreditosRepository
from db.repositories.liquidaciones_repo import LiquidacionesRepository
from db.repositories.recibos_repo import RecibosRepository
from db.repositories.auxiliar_repo import AuxiliarRepository
from db.repositories.config_repo import ConfigRepository


class DBManager:
    # Caché corta de la lista de socios: colapsa las consultas repetidas que
    # disparan varios formularios/vistas en la misma ráfaga de refresco. Con la
    # base en la nube (~130 ms por consulta) esto evita muchos viajes de ida y
    # vuelta. Se invalida al crear/editar/eliminar socios o créditos.
    _MEMBERS_TTL = 4.0  # segundos

    def __init__(self, db_path=None):
        self._db = DBConnection(db_path)
        self.db_path = db_path
        self._schema = None
        self._migration = None
        self._socios = None
        self._creditos = None
        self._liquidaciones = None
        self._recibos = None
        self._auxiliar = None
        self._config = None
        self._cache_full = None       # get_all_members_full
        self._cache_short = None      # get_all_members
        self._cache_ts = 0.0

    def _members_cache_fresh(self):
        import time
        return (time.monotonic() - self._cache_ts) < self._MEMBERS_TTL

    def invalidate_members(self):
        """Fuerza recargar la lista de socios en la próxima consulta."""
        self._cache_full = None
        self._cache_short = None
        self._cache_ts = 0.0

    @property
    def conn(self):
        return self._db.conn

    # --- Accessors para app.py: construye servicios inyectando repos ---
    @property
    def db_conn(self): return self._db
    @property
    def config_repo(self): return self._config
    @property
    def auxiliar_repo(self): return self._auxiliar
    @property
    def liquidaciones_repo(self): return self._liquidaciones
    @property
    def creditos_repo(self): return self._creditos
    @property
    def socios_repo(self): return self._socios

    def connect(self):
        result = self._db.connect()
        if result:
            self._schema = SchemaManager(self._db)
            self._migration = MigrationService(self._db, self._schema)
            self._socios = SociosRepository(self._db)
            self._creditos = CreditosRepository(self._db)
            self._liquidaciones = LiquidacionesRepository(self._db)
            self._recibos = RecibosRepository(self._db)
            self._auxiliar = AuxiliarRepository(self._db)
            self._config = ConfigRepository(self._db)
        return result

    # --- Schema / Migración (DESACTIVADOS contra la base compartida) ---
    # La estructura de la base la administra la API. Estos métodos se conservan
    # solo por compatibilidad de firma y NO deben ejecutarse: crear/alterar
    # tablas o reinicializar la config borraría datos reales (saldo_en_caja, etc.).
    def create_tables(self): self._schema.create_tables()
    def initialize_config_values(self): self._schema.initialize_config_values()
    def set_sequence_start_value(self, table_name, start_value): self._schema.set_sequence_start_value(table_name, start_value)
    def run_annual_migration(self, prev_db_path): self._migration.run_annual_migration(prev_db_path)

    # --- Socios ---
    def get_all_members(self):
        if self._cache_short is not None and self._members_cache_fresh():
            return self._cache_short
        import time
        self._cache_short = self._socios.find_all()
        self._cache_ts = time.monotonic()
        return self._cache_short

    def get_all_members_full(self):
        if self._cache_full is not None and self._members_cache_fresh():
            return self._cache_full
        import time
        self._cache_full = self._socios.find_all_full()
        self._cache_ts = time.monotonic()
        return self._cache_full
    def search_members_by_name(self, search_term): return self._socios.search_by_name(search_term)
    def get_member_by_id(self, member_id): return self._socios.find_by_id(member_id)
    def add_member(self, nombres, apellidos, phone, photo_path, saldo=0):
        self._socios.save(nombres, apellidos, phone, photo_path, saldo)
        self.invalidate_members()
    def update_member(self, socio_id, nombres, apellidos, phone, photo_path, nuevo_saldo):
        r = self._socios.update(socio_id, nombres, apellidos, phone, photo_path, nuevo_saldo)
        self.invalidate_members()
        return r
    def delete_member(self, socio_id):
        r = self._socios.delete(socio_id)
        self.invalidate_members()
        return r
    def member_history_counts(self, socio_id): return self._socios.history_counts(socio_id)

    # --- Creditos (solo lectura para vistas) ---
    def get_active_credits_by_member(self, member_id): return self._creditos.find_active_by_socio_id(member_id)
    def get_letras_by_socio_id(self, socio_id): return self._creditos.find_active_by_socio_id(socio_id)
    def get_credit_by_letra(self, letra): return self._creditos.find_by_letra(letra)
    def add_historical_credit(self, letra, capital, interes, no_cuotas, fecha_inicio, socios_ids, cuotas_data): return self._creditos.save_historical(letra, capital, interes, no_cuotas, fecha_inicio, socios_ids, cuotas_data)
    def add_manual_credit(self, socio_ids, capital, interes, n_cuotas, cuota_inicial, fecha_inicio=None):
        r = self._creditos.register_manual(socio_ids, capital, interes, n_cuotas, cuota_inicial, fecha_inicio)
        self.invalidate_members()  # cambia el conteo de créditos por socio
        return r

    def rebalance_credit_installments(self, letra_id, overrides):
        return self._liquidaciones.rebalance_installments(letra_id, overrides)

    # --- Numeración: recibo y letra actuales ---------------------------------
    # Permite fijar "en qué número vamos" (recibo y letra). Una vez fijado, el
    # sistema sigue automático desde ahí. Útil para armar el historial.
    def get_next_recibo(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COALESCE(MAX(id), 0) + 1 AS n FROM recibos")
        return int(cur.fetchone()["n"])

    def get_next_letra(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COALESCE(MAX(letra), 0) + 1 AS n FROM creditos")
        return int(cur.fetchone()["n"])

    def set_next_recibo(self, numero):
        """Fija el número del PRÓXIMO recibo. De ahí sigue automático."""
        self._reiniciar_secuencia("recibos", "id", numero)

    def set_next_letra(self, numero):
        """Fija el número de la PRÓXIMA letra. De ahí sigue automático."""
        self._reiniciar_secuencia("creditos", "letra", numero)

    def _reiniciar_secuencia(self, tabla, columna, numero):
        numero = int(numero)
        if numero < 1:
            raise ValueError("El número debe ser mayor o igual a 1.")
        cur = self.conn.cursor()
        # lock_timeout: si otra ventana/operación tiene la tabla ocupada, falla
        # rápido con un aviso en vez de colgar la app.
        cur.execute("SET LOCAL lock_timeout = '5s'")
        # tabla/columna son constantes internas (no input del usuario); numero
        # es un int validado. ALTER no acepta parámetros, por eso va formateado.
        cur.execute(f"ALTER TABLE {tabla} ALTER COLUMN {columna} RESTART WITH {numero}")
        self.conn.commit()

    # --- Inicio: próximos pagos, mora y movimientos ---
    def upcoming_installments(self, limit=5, dias=30):
        from config import get_hoy
        from datetime import timedelta
        hoy = get_hoy()
        hasta = (hoy + timedelta(days=dias)).strftime("%Y-%m-%d")
        return self._liquidaciones.find_upcoming(hoy.strftime("%Y-%m-%d"), hasta, limit)

    def overdue_installments(self, limit=5):
        from config import get_hoy_str
        return self._liquidaciones.find_overdue(get_hoy_str(), limit)

    def recent_movements(self, limit=5):
        return self._auxiliar.find_all(limit=limit)

    # --- Dashboard de datos ---
    def dashboard_metrics(self):
        """Devuelve un dict con los indicadores del tablero de datos.

        Todos los indicadores escalares se calculan en UNA sola consulta con
        subconsultas (un único viaje a la base en vez de ~9), y la tendencia y
        los mayores deudores en una consulta cada una: 3 viajes en total.
        """
        from config import get_hoy_str
        hoy = get_hoy_str()
        mes = hoy[:7]
        cur = self.conn.cursor()

        recaudo_tipos = ["Aporte", "Pago Credito", "Abono Capital"]

        def _i(v):
            return int(v) if v is not None else 0

        # 1) Todos los indicadores en un solo SELECT.
        cur.execute("""
            WITH prox AS (
                SELECT credito_letra, MIN(nro_cuota) AS nro
                FROM liquidaciones WHERE fecha_pago IS NULL GROUP BY credito_letra
            )
            SELECT
              (SELECT value FROM config WHERE key = 'saldo_en_caja') AS saldo_caja,
              (SELECT value FROM config WHERE key = 'total_admin')   AS papeleria,
              (SELECT COALESCE(SUM(abono_mora),0) FROM detalle_recibo) AS mora_acumulada,
              (SELECT COALESCE(SUM(saldo),0) FROM socios) AS aportes_socios,
              (SELECT COUNT(*) FROM socios) AS socios_activos,
              (SELECT COUNT(DISTINCT credito_letra) FROM liquidaciones WHERE fecha_pago IS NULL) AS creditos_vigentes,
              (SELECT COUNT(DISTINCT credito_letra) FROM liquidaciones
                 WHERE fecha_pago IS NULL AND fecha_vencimiento < %s) AS creditos_en_mora,
              (SELECT COALESCE(SUM(monto),0) FROM auxiliar
                 WHERE tipo = ANY(%s) AND substr(fecha,1,7) = %s) AS recaudo_mes,
              (SELECT COALESCE(SUM(l.saldo_capital + l.valor_cuota),0)
                 FROM prox p JOIN liquidaciones l
                 ON l.credito_letra = p.credito_letra AND l.nro_cuota = p.nro) AS cartera
        """, (hoy, recaudo_tipos, mes))
        m = cur.fetchone()

        saldo_caja = _i(m["saldo_caja"])
        papeleria = _i(m["papeleria"])
        mora_acumulada = _i(m["mora_acumulada"])
        aportes_socios = _i(m["aportes_socios"])
        socios_activos = _i(m["socios_activos"])
        creditos_vigentes = _i(m["creditos_vigentes"])
        creditos_en_mora = _i(m["creditos_en_mora"])
        recaudo_mes = _i(m["recaudo_mes"])
        cartera = _i(m["cartera"])

        # 2) Tendencia por mes.
        cur.execute(
            "SELECT substr(fecha,1,7) AS mes, COALESCE(SUM(monto),0) AS total FROM auxiliar "
            "WHERE tipo = ANY(%s) GROUP BY substr(fecha,1,7) ORDER BY mes DESC LIMIT 6",
            (recaudo_tipos,))
        tendencia = [{"mes": r["mes"], "total": int(r["total"] or 0)} for r in cur.fetchall()][::-1]

        # 3) Mayores deudores.
        cur.execute(
            "WITH prox AS (SELECT credito_letra, MIN(nro_cuota) AS nro "
            "FROM liquidaciones WHERE fecha_pago IS NULL GROUP BY credito_letra) "
            "SELECT l.credito_letra, (l.saldo_capital + l.valor_cuota) AS deuda, "
            "STRING_AGG(s.nombres || ' ' || s.apellidos, ', ') AS socios "
            "FROM prox p JOIN liquidaciones l "
            "ON l.credito_letra = p.credito_letra AND l.nro_cuota = p.nro "
            "JOIN socio_credito sc ON sc.credito_letra = l.credito_letra "
            "JOIN socios s ON s.id = sc.socio_id "
            "GROUP BY l.credito_letra, l.saldo_capital, l.valor_cuota "
            "ORDER BY deuda DESC LIMIT 5")
        mayores_deudores = [
            {"letra": r["credito_letra"], "deuda": int(r["deuda"] or 0), "socios": r["socios"]}
            for r in cur.fetchall()
        ]

        return {
            "saldo_caja": saldo_caja,
            "aportes_socios": aportes_socios,
            "cartera": cartera,
            "administracion": papeleria + mora_acumulada,
            "papeleria": papeleria,
            "mora_acumulada": mora_acumulada,
            "socios_activos": socios_activos,
            "creditos_vigentes": creditos_vigentes,
            "creditos_en_mora": creditos_en_mora,
            "creditos_al_dia": max(creditos_vigentes - creditos_en_mora, 0),
            "recaudo_mes": recaudo_mes,
            "tendencia": tendencia,
            "mayores_deudores": mayores_deudores,
        }

    def dashboard_charts(self, meses=12, top_n=10):
        """Datasets para las gráficas ampliadas del tablero (solo lectura).

        Devuelve, en pocas consultas:
          - aportes_mes / intereses_mes: series mensuales (últimos `meses`).
          - aportes_socio / intereses_socio: ranking por socio (Top `top_n`).
          - aportes_total / intereses_total: acumulados históricos.

        Aportes: se leen de `auxiliar`/`detalle_recibo` (tipo 'Aporte'/'aporte').
        Intereses: la parte de interés de cada cuota pagada vive en
        `liquidaciones.interes_mes`; el socio que paga se toma de
        `detalle_recibo.socio_id` (tipo_operacion 'pago_credito').
        """
        cur = self.conn.cursor()

        # 1) Aportes por mes.
        cur.execute(
            "SELECT substr(fecha,1,7) AS mes, COALESCE(SUM(monto),0) AS total "
            "FROM auxiliar WHERE tipo = 'Aporte' "
            "GROUP BY substr(fecha,1,7) ORDER BY mes DESC LIMIT %s", (meses,))
        aportes_mes = [{"mes": r["mes"], "total": int(r["total"] or 0)}
                       for r in cur.fetchall()][::-1]

        # 2) Intereses pagados por mes (cuotas ya pagadas).
        cur.execute(
            "SELECT substr(fecha_pago,1,7) AS mes, COALESCE(SUM(interes_mes),0) AS total "
            "FROM liquidaciones WHERE fecha_pago IS NOT NULL "
            "GROUP BY substr(fecha_pago,1,7) ORDER BY mes DESC LIMIT %s", (meses,))
        intereses_mes = [{"mes": r["mes"], "total": int(r["total"] or 0)}
                         for r in cur.fetchall()][::-1]

        # 3) Aportes por socio (Top N).
        cur.execute(
            "SELECT s.nombres || ' ' || s.apellidos AS socio, COALESCE(SUM(dr.monto),0) AS total "
            "FROM detalle_recibo dr JOIN socios s ON s.id = dr.socio_id "
            "WHERE dr.tipo_operacion = 'aporte' "
            "GROUP BY s.id, s.nombres, s.apellidos ORDER BY total DESC LIMIT %s", (top_n,))
        aportes_socio = [{"socio": r["socio"], "total": int(r["total"] or 0)}
                         for r in cur.fetchall()]

        # 4) Intereses pagados por socio (Top N): interés de cada cuota pagada,
        #    atribuido al socio que registró el pago.
        cur.execute(
            "SELECT s.nombres || ' ' || s.apellidos AS socio, COALESCE(SUM(l.interes_mes),0) AS total "
            "FROM detalle_recibo dr "
            "JOIN liquidaciones l ON l.credito_letra = dr.credito_letra AND l.nro_cuota = dr.nro_cuota "
            "JOIN socios s ON s.id = dr.socio_id "
            "WHERE dr.tipo_operacion = 'pago_credito' AND dr.nro_cuota > 0 "
            "GROUP BY s.id, s.nombres, s.apellidos ORDER BY total DESC LIMIT %s", (top_n,))
        intereses_socio = [{"socio": r["socio"], "total": int(r["total"] or 0)}
                           for r in cur.fetchall()]

        # 5) Acumulados históricos.
        cur.execute("SELECT COALESCE(SUM(interes_mes),0) AS t FROM liquidaciones WHERE fecha_pago IS NOT NULL")
        intereses_total = int(cur.fetchone()["t"] or 0)
        cur.execute("SELECT COALESCE(SUM(monto),0) AS t FROM detalle_recibo WHERE tipo_operacion = 'aporte'")
        aportes_total = int(cur.fetchone()["t"] or 0)

        return {
            "aportes_mes": aportes_mes,
            "intereses_mes": intereses_mes,
            "aportes_socio": aportes_socio,
            "intereses_socio": intereses_socio,
            "aportes_total": aportes_total,
            "intereses_total": intereses_total,
        }

    def add_multiple_historical_credits(self, credits_list):
        print(f"\n📋 Iniciando carga masiva de {len(credits_list)} créditos...\n")
        resultados = []
        for i, credit in enumerate(credits_list, 1):
            letra_especifica = credit.get("letra")
            print(f"[{i}/{len(credits_list)}] Procesando Letra: {letra_especifica}")
            res = self._creditos.save_historical(
                letra=letra_especifica,
                capital=credit["capital"],
                interes=credit["interes"],
                no_cuotas=credit["no_cuotas"],
                fecha_inicio=credit["fecha_inicio"],
                socios_ids=credit["socios_ids"],
                cuotas_data=credit["cuotas"],
            )
            resultados.append(res)
        exitosos = len([l for l in resultados if l])
        print(f"\n✅ Proceso finalizado: {exitosos} créditos creados correctamente.")
        return resultados

    # --- Auxiliar (solo lectura para vistas) ---
    def get_auxiliary_operations(self, limit=10, offset=0, start_date=None, end_date=None, operation_type=None, socio_name=None, numero=None, letra_credito=None): return self._auxiliar.find_all(limit, offset, start_date, end_date, operation_type, socio_name, numero, letra_credito)
    def delete_auxiliary_operation(self, op_id): return self._auxiliar.delete(op_id)
