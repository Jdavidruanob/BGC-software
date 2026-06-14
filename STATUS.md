# BGC Software — Estado del Proyecto

> Última actualización: 2026-06-13  
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
| *(pendiente)* | Fase 3: Desacoplar servicios de `db_manager` — inyección directa de repos |

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

## Lo que ya está hecho — Fase 3 ✅

La Fase 3 desacopló completamente los **servicios** de `db_manager`. Los servicios
ahora reciben repos individuales; `db_manager` queda como fachada de solo lectura
para las vistas que aún no fueron migradas.

### Cambios realizados en Fase 3

| Archivo | Cambio |
|---|---|
| `db/db_manager.py` | Añadidos property accessors (`db_conn`, `config_repo`, `auxiliar_repo`, `liquidaciones_repo`, `creditos_repo`). Eliminados ~20 métodos de escritura (solo los usaban los servicios). |
| `services/aporte_service.py` | Constructor `(db, config, auxiliar)` — usa repos directamente. |
| `services/retiro_service.py` | Constructor `(db, config, auxiliar)`. |
| `services/credito_service.py` | Constructor `(db, creditos, auxiliar, config)`. |
| `services/pago_service.py` | Constructor `(db, liquidaciones, auxiliar, config)`. |
| `services/combinado_service.py` | Constructor `(db, liquidaciones, auxiliar, config)`. |
| `services/caja_service.py` | Constructor `(config, auxiliar)` — sin `DBConnection`. |
| `utils/recibo_generator_aporte.py` | Eliminado parámetro `db_manager` (nunca se usaba). |
| `utils/recibo_generator_pago.py` | `db_manager` → `get_total_cuotas: callable`. |
| `utils/recibo_generator_combinado.py` | `db_manager` → `get_total_cuotas: callable`. |
| `views/widgets/forms/form_*.py` | Constructores reciben `service` pre-construido en lugar de instanciarlo. |
| `views/home_page.py` | Constructor recibe 6 servicios + `db_manager`. Pasa cada servicio a su form. |
| `app.py` | Construye servicios inyectando repos via `db_manager.config_repo` etc., luego pasa servicios a `HomePage`. |

### Estado de `db_manager` después de Fase 3

`db_manager` permanece como fachada **de solo lectura** para las vistas que no fueron
migradas (members_page, member_detail_page, assistant_page, liquidation_page). Estas
vistas usan solo `get_all_members`, `get_member_by_id`, `get_auxiliary_operations`,
`conn.cursor()` etc. — nada de escritura.

Si en el futuro se quiere eliminar `db_manager` del todo, el paso sería migrar esas
vistas a recibir repos directamente. No es prioritario.

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
