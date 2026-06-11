"""
Fachada de compatibilidad. Delega a los repositorios del paquete db/.
En Fase 2, las vistas pasarán a usar los servicios directamente y esta clase se eliminará.
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
    def __init__(self, db_path):
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

    @property
    def conn(self):
        return self._db.conn

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

    # --- Schema ---
    def create_tables(self): self._schema.create_tables()
    def initialize_config_values(self): self._schema.initialize_config_values()
    def set_sequence_start_value(self, table_name, start_value): self._schema.set_sequence_start_value(table_name, start_value)

    # --- Migration ---
    def run_annual_migration(self, prev_db_path): self._migration.run_annual_migration(prev_db_path)

    # --- Socios ---
    def get_all_members(self): return self._socios.find_all()
    def get_all_members_full(self): return self._socios.find_all_full()
    def search_members_by_name(self, search_term): return self._socios.search_by_name(search_term)
    def get_member_by_id(self, member_id): return self._socios.find_by_id(member_id)
    def get_member_balance(self, member_id): return self._socios.get_balance(member_id)
    def add_member(self, nombres, apellidos, phone, photo_path, saldo=0): self._socios.save(nombres, apellidos, phone, photo_path, saldo)
    def update_member(self, socio_id, nombres, apellidos, phone, photo_path, nuevo_saldo): return self._socios.update(socio_id, nombres, apellidos, phone, photo_path, nuevo_saldo)
    def delete_member(self, socio_id): return self._socios.delete(socio_id)

    # --- Creditos ---
    def add_credit(self, socio_ids, capital, interes, no_cuotas): return self._creditos.save(socio_ids, capital, interes, no_cuotas)
    def get_active_credits_by_member(self, member_id): return self._creditos.find_active_by_socio_id(member_id)
    def get_letras_by_socio_id(self, socio_id): return self._creditos.find_active_by_socio_id(socio_id)
    def get_credit_by_letra(self, letra): return self._creditos.find_by_letra(letra)
    def update_credit_installments(self, letra_id, new_total_cuotas): return self._creditos.update_installments(letra_id, new_total_cuotas)
    def add_historical_credit(self, letra, capital, interes, no_cuotas, fecha_inicio, socios_ids, cuotas_data): return self._creditos.save_historical(letra, capital, interes, no_cuotas, fecha_inicio, socios_ids, cuotas_data)
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
    def registrar_credito_completo(self, socio_ids, capital, interes_tasa, n_cuotas, usuario_tesorero="ALVARO L. BURBANO GARCIA"): return self._creditos.register_complete(socio_ids, capital, interes_tasa, n_cuotas)

    # --- Liquidaciones ---
    def guardar_liquidaciones(self, lista_cuotas): self._liquidaciones.save_all(lista_cuotas)
    def get_total_cuotas_credito(self, credito_letra): return self._liquidaciones.get_total_cuotas(credito_letra)
    def get_pending_installments(self, letra_id): return self._liquidaciones.find_pending(letra_id)
    def get_deuda_capital_actual(self, letra_id): return self._liquidaciones.get_current_debt(letra_id)
    def recalcular_tabla_amortizacion(self, letra_id, abono_capital_recien_registrado): self._liquidaciones.recalculate_amortization(letra_id, abono_capital_recien_registrado)

    # --- Recibos ---
    def create_aporte_recibo(self, recibi_de_id, aportes): return self._recibos.create_aporte(recibi_de_id, aportes)

    # --- Auxiliar ---
    def add_to_auxiliar(self, fecha, tipo, socio, monto, saldo, recibo=None, cuota=None, id_credito=None): self._auxiliar.add(fecha, tipo, socio, monto, saldo, recibo, cuota, id_credito)
    def get_auxiliary_operations(self, limit=10, offset=0, start_date=None, end_date=None, operation_type=None, socio_name=None, numero=None, letra_credito=None): return self._auxiliar.find_all(limit, offset, start_date, end_date, operation_type, socio_name, numero, letra_credito)
    def delete_auxiliary_operation(self, op_id): return self._auxiliar.delete(op_id)

    # --- Config ---
    def get_config_value(self, key): return self._config.get(key)
    def get_config_value_as_int(self, key): return self._config.get_int(key)
    def set_config_value(self, key, value): self._config.set(key, value)
