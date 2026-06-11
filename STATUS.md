# BGC Software — Estado del Proyecto

> Última actualización: 2026-06-10  
> Rama activa: `develop`

---

## Contexto

El proyecto es una aplicación de escritorio para gestión financiera de una cooperativa.
El código original fue escrito sin AI y tenía problemas de calidad: una god-class de 1279
líneas (`db_manager.py`), lógica de negocio mezclada en los forms, SQL directo en la UI,
y commits/rollbacks repartidos por todos lados.

El objetivo del refactor es: **mantener funcionalidad exacta, mejorar estructura de
código siguiendo SOLID (SRP, DIP), sin sobreingeniería**.

---

## Historial de commits del refactor

| Commit | Descripción |
|---|---|
| `b72ebf7` | Fase 0: Modularizar estilos QSS — `shared.qss`, `PRIMARY_HOVER_COLOR`, `ui_helpers.py` |
| `4dbe0be` | Fase 1: Extraer repositorios de `db_manager.py` |
| `f72c9b5` | Fase 2a: Crear capa de servicios (7 archivos) |
| `d70e8b7` | Fase 2b: Migrar vistas a usar los servicios |

---

## Lo que ya está hecho

### Fase 0 — Estilos
- `styles/shared.qss` centraliza variables de color y estilos base.
- `PRIMARY_HOVER_COLOR` añadido a `config.py`.
- `views/widgets/ui_helpers.py` con factories de widgets reutilizables.
- Inconsistencias de color corregidas en todas las vistas.

### Fase 1 — Repositorios
`db/db_manager.py` pasó de 1279 líneas (god-class) a ~110 líneas (fachada).
La lógica de acceso a datos vive ahora en:

| Archivo | Responsabilidad |
|---|---|
| `db/connection.py` | `DBConnection`: solo `sqlite3.connect` + `row_factory` |
| `db/schema.py` | `SchemaManager`: `CREATE TABLE`, init config, secuencias |
| `db/migration.py` | `MigrationService`: migración anual de saldos |
| `db/repositories/socios_repo.py` | CRUD socios, búsqueda, delete en cascada |
| `db/repositories/creditos_repo.py` | CRUD créditos, cotitulares, `register_complete` (amortización) |
| `db/repositories/liquidaciones_repo.py` | CRUD cuotas, `recalculate_amortization` |
| `db/repositories/recibos_repo.py` | Inserción de recibos |
| `db/repositories/auxiliar_repo.py` | Log auxiliar |
| `db/repositories/config_repo.py` | Key-value config |

**Limpieza realizada en Fase 1:**
- Eliminado `get_recibo` (stub vacío).
- Eliminado `debug_check_auxiliar`.
- Eliminados bloques comentados de sync de `saldo_en_caja`.
- Unificados `get_active_credits_by_member` y `get_letras_by_socio_id`
  → un solo `find_active_by_socio_id`.
- Funciones muertas `add_historical_credit` / `add_multiple_historical_credits`
  que estaban en `config.py` como funciones de módulo con `self` (código muerto) — eliminadas.
- `app.py`: reducido de 1840 a ~120 líneas (extraído bloque de 1700 líneas de
  créditos históricos a `scripts/seed_historical_credits.py`).
- `scripts/seed_members.py`: 54 socios fundadores extraídos.

### Fase 2a — Servicios
Creados en `services/`:

| Archivo | Método principal | Retorna |
|---|---|---|
| `amortization.py` | `calculate_mora`, `round_installments`, `build_amortization_schedule` | funciones puras |
| `aporte_service.py` | `register(recibi_de_id, recibi_data, aportes, count_cobrables)` | `(recibo_id, excel_path)` |
| `retiro_service.py` | `register(socio_id, socio_data, monto)` | `(recibo_id, excel_path, nuevo_saldo_caja)` |
| `credito_service.py` | `create(socio_ids, capital, interes_tasa, n_cuotas, socios_data)` | `(letra_id, excel_path)` |
| `pago_service.py` | `register(recibi_de_id, recibi_data, pagos_input)` | `(recibo_id, excel_path, reporte_global)` |
| `combinado_service.py` | `register(recibi_de_id, recibi_data, aportes_input, pagos_input, count_cobrables)` | `(recibo_id, excel_path, reporte_global)` |
| `caja_service.py` | `get_saldo_caja`, `get_total_admin`, `get_porcentaje_mora`, `adjust_caja`, `set_admin_config` | varios |

Cada servicio maneja su propia transacción (`try / rollback / commit`).
Los errores de validación de negocio se lanzan como `ValueError` con mensaje descriptivo.

### Fase 2b — Migración de vistas
Las siguientes vistas fueron migradas para delegar toda la lógica de negocio a sus servicios:

| Vista | Servicio usado | Líneas eliminadas (aprox.) |
|---|---|---|
| `views/widgets/forms/form_aporte.py` | `AporteService` | ~80 |
| `views/widgets/forms/form_retiro.py` | `RetiroService` | ~65 |
| `views/widgets/forms/form_nuevo_credito.py` | `CreditoService` | ~50 |
| `views/widgets/forms/form_pago_credito.py` | `PagoService` | ~300 |
| `views/widgets/forms/form_combinado.py` | `CombinadoService` | ~390 |
| `views/home_page.py` | `CajaService` | ~25 |

Total: ~790 líneas de lógica de negocio/SQL eliminadas de la UI.

---

## Lo que falta — Fase 3

La Fase 3 es la última del refactor. **No cambia ningún comportamiento, solo limpia
la estructura de dependencias.**

### 3.1 — Eliminar la fachada `db_manager.py`

**Por qué existe todavía:** los servicios usan `db_manager` porque los generadores
de Excel (`utils/`) llaman a `db_manager.get_total_cuotas_credito()`. Hay que pasar
ese método directamente al generador o inyectarlo de otra forma.

**Pasos:**
1. Auditar qué métodos de `db_manager` sigue usando cada servicio y cada vista.
2. Hacer que los servicios reciban los repos que necesitan directamente, en lugar
   de la fachada completa.
3. Ajustar los generadores de Excel para que no dependan de `db_manager`.
4. Eliminar `db/db_manager.py`.

### 3.2 — Limpiar el wiring en `app.py`

Con la fachada eliminada, `app.py` instancia `DBConnection`, repos y servicios
y los inyecta en las vistas:

```python
# Esquema objetivo de app.py
db = DBConnection(DB_PATH_FINAL)
db.connect()

schema = SchemaManager(db)
schema.create_tables()

# Repos
socios = SociosRepository(db)
creditos = CreditosRepository(db)
liquidaciones = LiquidacionesRepository(db)
auxiliar = AuxiliarRepository(db)
config_repo = ConfigRepository(db)

# Servicios
aporte_svc = AporteService(socios, auxiliar, config_repo)
retiro_svc = RetiroService(socios, auxiliar, config_repo)
credito_svc = CreditoService(creditos, liquidaciones, auxiliar, config_repo)
pago_svc = PagoService(liquidaciones, auxiliar, config_repo)
combinado_svc = CombinadoService(socios, liquidaciones, auxiliar, config_repo)
caja_svc = CajaService(auxiliar, config_repo)

# Vistas
window = MainWindow()
assistant_page = AssistantPage(auxiliar)
home_page = HomePage(aporte_svc, retiro_svc, pago_svc, credito_svc, combinado_svc, caja_svc, assistant_page, window)
...
```

### 3.3 — Revisar vistas restantes que acceden a `db_manager` directamente

Las siguientes vistas aún no han sido migradas (no tienen equivalente en los servicios
actuales). En Fase 3 deben revisarse:

| Vista | Acceso actual a db_manager | Acción sugerida |
|---|---|---|
| `views/members_page.py` | `get_all_members`, `search_members_by_name` | Inyectar `SociosRepository` directamente |
| `views/member_detail_page.py` | `get_member_by_id`, `get_active_credits_by_member`, `update_member`, `delete_member` | Inyectar `SociosRepository` + `CreditosRepository` |
| `views/assistant_page.py` | `get_auxiliary_operations`, `delete_auxiliary_operation` | Inyectar `AuxiliarRepository` |
| `views/liquidation_page.py` | `get_pending_installments`, `get_credit_by_letra` | Inyectar `LiquidacionesRepository` + `CreditosRepository` |
| `views/home_page.py` (resumen) | `get_all_members_full`, SQL para créditos activos | Inyectar repos o exponer método en `CajaService` |

> Nota: estas vistas son de solo lectura (no modifican datos), por lo que inyectar
> repos directamente es aceptable — no necesitan pasar por un servicio.

---

## Decisiones de diseño tomadas

- **Sin ABCs ni DI framework**: clases simples, wiring manual en `app.py`.
- **Fachada temporal**: `db_manager` sigue existiendo hasta Fase 3 para no romper
  las vistas de solo lectura que aún no se migraron.
- **Servicios con `db_manager`**: transitoriamente, los servicios reciben `db_manager`
  en lugar de repos individuales. Se arregla en Fase 3.
- **Generadores de Excel intocables**: las plantillas `.xlsx` tienen columnas fijas.
  Los generadores de `utils/` no deben restructurarse — solo sus dependencias.
- **Transacciones en servicios**: cada método de servicio hace un solo `commit()`.
  Los repos no hacen `commit()` nunca.
- **`populate_initial_members`** → extraído a `scripts/seed_members.py`.
- **`add_multiple_historical_credits`** → extraído a `scripts/seed_historical_credits.py`.
- **Cálculo de mora**: período de gracia de 1 mes. `mora = int(valor_cuota * tasa_mora)`
  solo si `hoy > vencimiento + 1 mes`.
- **La mora va a `total_admin`, no a `saldo_en_caja`**. Este es el invariante
  financiero más importante del sistema.

---

## Verificación antes de continuar

Después de cualquier cambio ejecutar:
1. `python app.py` — la app debe arrancar sin errores.
2. Registrar un aporte → verificar recibo Excel generado y saldo actualizado.
3. Pagar una cuota de crédito → verificar mora si aplica y que el recibo incluya el total.
4. Crear un crédito nuevo → verificar la tabla de amortización en Excel.
5. Usar el formulario combinado → verificar que papelería y mora se distribuyan correctamente.
