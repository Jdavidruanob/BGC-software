# BGC Software — Especificación del Proyecto

## Descripción general

Aplicación de escritorio para la gestión financiera de una cooperativa de ahorro (BGC).
Permite registrar aportes de socios, pagos de créditos, retiros, nuevos créditos y
consultar el historial contable. Cada operación genera un recibo en Excel a partir de
plantillas preexistentes.

**Tecnología:** Python 3.14, PySide6 (Qt), SQLite (sin ORM), openpyxl.

---

## Stack

| Capa | Tecnología |
|---|---|
| UI | PySide6 6.11 (QWidget, no QML) |
| Base de datos | SQLite 3 vía `sqlite3` estándar |
| Excel | openpyxl — plantillas `.xlsx` en `assets/templates/` |
| Estilos | QSS cargado dinámicamente con interpolación `%(var)s` |
| Fechas | `python-dateutil` para relativedelta (vencimientos) |
| Empaquetado | PyInstaller (`build.py`) |

---

## Estructura de archivos

```
BGC-software/
├── app.py                        # Punto de entrada: wiring manual, arranque de Qt
├── config.py                     # Constantes globales, rutas, utilidades UI y fecha
├── requirements.txt
├── build.py                      # Script PyInstaller
│
├── db/
│   ├── connection.py             # DBConnection: sqlite3.connect + row_factory
│   ├── schema.py                 # SchemaManager: CREATE TABLE, init config, secuencias
│   ├── migration.py              # MigrationService: migración anual de saldos
│   ├── db_manager.py             # Fachada de solo lectura para vistas; los servicios usan repos directamente
│   └── repositories/
│       ├── socios_repo.py        # CRUD socios
│       ├── creditos_repo.py      # CRUD créditos + socio_credito + register_complete
│       ├── liquidaciones_repo.py # CRUD cuotas + recalculate_amortization
│       ├── recibos_repo.py       # Inserción de recibos
│       ├── auxiliar_repo.py      # Log contable auxiliar
│       └── config_repo.py        # Tabla key-value de configuración
│
├── services/
│   ├── amortization.py           # Funciones puras: mora, redondeo, tabla de cuotas
│   ├── aporte_service.py         # Registrar aportes (transacción + Excel)
│   ├── retiro_service.py         # Registrar retiros
│   ├── credito_service.py        # Crear crédito + amortización
│   ├── pago_service.py           # Pagar cuotas / abono cascada
│   ├── combinado_service.py      # Aportes + pagos en una sola transacción
│   └── caja_service.py           # Leer/ajustar saldo en caja y config admin
│
├── views/
│   ├── main_window.py            # Ventana principal con navegación lateral
│   ├── home_page.py              # Panel principal: formularios + resumen financiero
│   ├── assistant_page.py         # Historial auxiliar con filtros y paginación
│   ├── members_page.py           # Lista de socios con búsqueda
│   ├── member_detail_page.py     # Detalle de socio: saldo, créditos activos
│   ├── liquidation_page.py       # Vista de tabla de amortización de un crédito
│   ├── data_page.py              # Página de datos / importación
│   └── widgets/
│       ├── forms/
│       │   ├── form_aporte.py         # Formulario de aportes
│       │   ├── form_retiro.py         # Formulario de retiros
│       │   ├── form_nuevo_credito.py  # Formulario nuevo crédito
│       │   ├── form_pago_credito.py   # Formulario pago de crédito
│       │   └── form_combinado.py      # Formulario combinado (aporte + pago)
│       ├── adjust_balance_dialog.py   # Diálogo para ajuste manual de caja
│       ├── edit_admin_dialog.py       # Diálogo para papelería y tasa de mora
│       ├── new_member_dialog.py       # Diálogo alta de socio
│       ├── credit_card_widget.py      # Tarjeta de crédito en detalle de socio
│       ├── member_card.py             # Tarjeta de socio en lista
│       ├── comboBox_custom.py         # ComboBox sin scroll accidental
│       └── ui_helpers.py             # Factories de widgets reutilizables
│
├── utils/
│   ├── message_boxes.py               # show_success, show_error, show_warning, show_info
│   ├── recibo_generator_aporte.py     # Genera Excel de recibo de aportes
│   ├── recibo_generator_retiro.py     # Genera Excel de recibo de retiro
│   ├── recibo_generator_pago.py       # Genera Excel de recibo de pago de crédito
│   ├── recibo_generator_combinado.py  # Genera Excel de recibo combinado
│   └── credit_liquidation_generator.py # Genera Excel de tabla de amortización
│
├── styles/
│   ├── shared.qss              # Estilos base compartidos por todos los componentes
│   ├── main_window.qss
│   ├── home_page.qss
│   └── forms/
│       ├── form_aporte.qss
│       ├── form_retiro.qss
│       └── ...
│
├── assets/
│   ├── fonts/InterVariable.ttf
│   ├── icons/                  # SVGs (Lucide)
│   ├── photos/default_user.png
│   └── templates/              # Plantillas .xlsx para recibos y liquidaciones
│
└── scripts/
    ├── seed_members.py          # Carga inicial de 54 socios fundadores (one-shot)
    └── seed_historical_credits.py # Carga de créditos históricos (one-shot)
```

---

## Base de datos

### Tablas

**`socios`**
```
id          INTEGER PK AUTOINCREMENT
cc          TEXT
nombres     TEXT NOT NULL
apellidos   TEXT NOT NULL
saldo       INTEGER DEFAULT 0   ← suma de aportes - retiros
celular     TEXT
photo_path  TEXT
created_at  TIMESTAMP
```

**`creditos`**
```
letra       INTEGER PK AUTOINCREMENT   ← identificador del crédito
capital     INTEGER NOT NULL
interes     REAL NOT NULL              ← tasa mensual (ej. 0.01 = 1%)
no_cuotas   INTEGER NOT NULL
fecha_inicio TIMESTAMP
```

**`socio_credito`** — relación N:N (un crédito puede tener varios cotitulares)
```
socio_id        FK → socios.id
credito_letra   FK → creditos.letra
PK (socio_id, credito_letra)
```

**`liquidaciones`** — tabla de amortización (una fila por cuota)
```
id                  INTEGER PK AUTOINCREMENT
credito_letra       FK → creditos.letra
nro_cuota           INTEGER
fecha_vencimiento   DATE
valor_cuota         INTEGER    ← capital de esa cuota
interes_mes         INTEGER    ← interés de esa cuota
cuota_mensual       INTEGER    ← valor_cuota + interes_mes
saldo_capital       INTEGER    ← saldo restante tras esta cuota
fecha_pago          DATE       ← NULL si no pagada
interes_mora        INTEGER DEFAULT 0
mora_aplicada       INTEGER DEFAULT 0
```

**`recibos`**
```
id          INTEGER PK AUTOINCREMENT
socio_id    FK → socios.id
fecha       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
archivo_path TEXT
```

**`detalle_recibo`**
```
id              INTEGER PK AUTOINCREMENT
recibo_id       FK → recibos.id
tipo_operacion  TEXT CHECK IN ('aporte','pago_credito','retiro','abono_capital')
socio_id        FK → socios.id
credito_letra   FK → creditos.letra   (NULL para aportes/retiros)
nro_cuota       INTEGER               (0 para abono capital puro)
monto           INTEGER               ← total cobrado al socio (base + mora)
abono_mora      INTEGER DEFAULT 0     ← porción de mora en este monto
```

**`auxiliar`** — log cronológico de todos los movimientos de caja
```
id          INTEGER PK AUTOINCREMENT
fecha       TEXT
tipo        TEXT    ← 'Aporte', 'Retiro', 'Pago Credito', 'Abono Capital', 'Nuevo Credito', o texto libre (ajuste)
socio       TEXT
recibo      INTEGER
monto       INTEGER   ← positivo = entrada, negativo = salida
saldo       INTEGER   ← saldo_en_caja tras esta operación
cuota       INTEGER
id_credito  TEXT
```

**`config`** — tabla key-value de parámetros globales
```
key     TEXT PK
value   TEXT
```
Claves activas:
- `saldo_en_caja` — saldo total actual en caja (entero COP)
- `total_admin` — fondo de papelería acumulado (entero COP)
- `porcentaje_mora` — tasa de mora mensual como float (ej. `"0.02"`)

---

## Año fiscal

El año fiscal determina la carpeta donde se guardan la DB y los recibos:

```
Archivos_BGC/
└── {FISCAL_YEAR}/
    ├── BGC-software.db
    ├── Recibos/
    └── Liquidaciones/
```

- Si el mes actual es **diciembre**, el año fiscal = año siguiente.
- Si el mes es enero–noviembre, el año fiscal = año actual.
- Al iniciar la app sin DB del año fiscal actual, verifica si existe la carpeta
  del año anterior para ejecutar la **migración anual** (transferir saldos).

---

## Reglas de negocio

### Aportes
- Cada aporte incrementa `socios.saldo` y `saldo_en_caja`.
- Por cada aporte con el checkbox de papelería activo se suman **$3.000 COP** a `total_admin`.
- Un recibo puede tener hasta **6 aportes** (límite de la plantilla Excel).

### Retiros
- Solo se permite si `monto <= socios.saldo`.
- Decrementa `socios.saldo` y `saldo_en_caja`.
- El monto se registra como negativo en `auxiliar`.

### Créditos
- Al crear un crédito se descuenta el capital de `saldo_en_caja`.
- Se genera la tabla de amortización completa en `liquidaciones`.
- **Redondeo inteligente de cuota:** busca el primer divisor en `[10000, 9000, 8000, 7000, 6000, 5000, 2000, 1000]` tal que la última cuota quede entre `$10.000` y `cuota_base * 1.5`. La última cuota absorbe el residuo.
- Un crédito puede tener múltiples socios cotitulares (`socio_credito`).

### Pagos de crédito — dos modos

**Modo A: Cuotas manuales** (`n_cuotas > 0`)
- El usuario indica cuántas cuotas paga. Se toman las N primeras cuotas pendientes
  en orden (`ORDER BY nro_cuota`).
- Cada cuota cobra: `valor_cuota + interes_mes + mora` (si aplica).

**Modo B: Abono cascada** (`abono_capital > 0`)
- El usuario indica un monto. El sistema lo aplica primero a todas las cuotas
  **vencidas** (en orden cronológico) y el remanente se aplica como **abono a
  capital** en la tabla de amortización.
- Si el monto no alcanza para cubrir todas las cuotas vencidas parcialmente,
  se lanza `ValueError`.
- El abono a capital llama a `recalculate_amortization` que redistribuye el
  saldo entre las cuotas futuras.

### Mora
- Se aplica si `fecha_actual > fecha_vencimiento + 1 mes`.
- `mora = int(valor_cuota * tasa_mora)` donde `tasa_mora` viene de `config.porcentaje_mora`.
- La mora va a `total_admin`, **no** a `saldo_en_caja`.

### Distribución financiera por operación
| Operación | `saldo_en_caja` | `total_admin` |
|---|---|---|
| Aporte | +monto | +$3.000 × aportes_cobrables |
| Retiro | -monto | — |
| Nuevo crédito | -capital | — |
| Pago de cuota (base) | +(cap + interés) | — |
| Mora cobrada | — | +mora |
| Ajuste manual | +/- monto | — |

---

## Recibos Excel

Los generadores en `utils/` abren una plantilla `.xlsx` y rellenan celdas fijas
(sin cambiar columnas — las plantillas son intocables).

| Generador | Plantilla | Cuándo se usa |
|---|---|---|
| `recibo_generator_aporte.py` | `recibo_aportes.xlsx` | `form_aporte` |
| `recibo_generator_retiro.py` | `recibo_retiro.xlsx` | `form_retiro` |
| `recibo_generator_pago.py` | `recibo_pagos.xlsx` | `form_pago_credito` |
| `recibo_generator_combinado.py` | `recibo_combinado.xlsx` | `form_combinado` |
| `credit_liquidation_generator.py` | `liquidacion_credito.xlsx` | `form_nuevo_credito` |

Los archivos generados se guardan en `Archivos_BGC/{FISCAL_YEAR}/Recibos/`.

---

## Estilos QSS

- `config.load_styles(widget, qss_path)` carga `shared.qss` + el QSS del componente.
- La interpolación usa `%(VAR)s` con las constantes de color de `config.py`:
  - `PRIMARY_COLOR` — `#1a365d` (azul oscuro, navbar)
  - `PRIMARY_HOVER_COLOR` — `#2a4a80`
  - `SECONDARY_COLOR` — `#8C5B2F` (marrón, hover activo)
  - `TEXT_COLOR` — `#FFFFFF`

---

## Arquitectura de capas

```
┌─────────────────────────────────────┐
│  Views (PySide6 QWidgets)           │  Solo recolección de input y display
│  views/*, views/widgets/forms/*     │  Sin SQL, sin lógica de negocio
└──────┬──────────────────────────────┘
       │ forms llaman a                │ vistas de lectura usan
       ▼                              ▼
┌─────────────────┐        ┌──────────────────────┐
│  Services       │        │  DBManager (fachada)  │
│  services/      │        │  db/db_manager.py     │
│  Un commit()    │        │  Solo lectura para    │
│  por operación  │        │  members/assistant/   │
└───────┬─────────┘        │  liquidation pages    │
        │ inyectados       └──────────┬────────────┘
        ▼                             │
┌─────────────────────────────────────▼──────────┐
│  Repositories  (db/repositories/)              │
│  CRUD puro por dominio, sin commits            │
└───────────────────────┬────────────────────────┘
                        │
┌───────────────────────▼────────────────────────┐
│  DBConnection (db/connection.py)               │
│  sqlite3.connect + row_factory                 │
└────────────────────────────────────────────────┘
```

**Reglas invariantes de la arquitectura:**
- Los **repositorios** nunca hacen `commit()` ni tienen lógica de negocio.
- Los **servicios** orquestan repositorios, manejan la transacción completa (`try / rollback / commit`), y llaman a los generadores de Excel. Reciben repos individuales inyectados, no `db_manager`.
- Los **forms** reciben el servicio pre-construido en el constructor (inyectado desde `HomePage`). Solo hacen: recolectar input → llamar servicio → mostrar resultado.
- Las **vistas de lectura** (`members_page`, `member_detail_page`, `assistant_page`, `liquidation_page`) reciben `db_manager` directamente para consultas simples.
- Los `ValueError` de validación de negocio se lanzan desde servicios y se capturan en los forms con `show_error`.

---

## Wiring de dependencias (`app.py`)

```python
db_manager = DBManager(DB_PATH_FINAL)
db_manager.connect()
db_manager.create_tables()

# Servicios construidos inyectando repos desde db_manager
aporte_svc  = AporteService(db_manager.db_conn, db_manager.config_repo, db_manager.auxiliar_repo)
retiro_svc  = RetiroService(db_manager.db_conn, db_manager.config_repo, db_manager.auxiliar_repo)
credito_svc = CreditoService(db_manager.db_conn, db_manager.creditos_repo, db_manager.auxiliar_repo, db_manager.config_repo)
pago_svc    = PagoService(db_manager.db_conn, db_manager.liquidaciones_repo, db_manager.auxiliar_repo, db_manager.config_repo)
combinado_svc = CombinadoService(db_manager.db_conn, db_manager.liquidaciones_repo, db_manager.auxiliar_repo, db_manager.config_repo)
caja_svc    = CajaService(db_manager.config_repo, db_manager.auxiliar_repo)

window = MainWindow()
assistant_page = AssistantPage(db_manager)
home_page = HomePage(aporte_svc, retiro_svc, pago_svc, credito_svc, combinado_svc,
                     caja_svc, db_manager, assistant_page, window)

window.add_view("home", home_page)
window.add_view("assistant", assistant_page)
window.add_view("members", MembersPage(db_manager, window))
window.add_view("data", DataPage())
```

`HomePage` instancia los forms pasándoles el servicio ya construido:
```python
self.form_aporte      = FormAporte(aporte_svc, self.db_manager, self.assistant_page)
self.page_pago        = FormPagoCredito(pago_svc, self.db_manager, self.assistant_page)
self.form_nuevo_credito = FormNuevoCredito(credito_svc, self.db_manager, self.main_window, ...)
self.form_retiro      = FormRetiro(retiro_svc, self.db_manager)
self.form_aporte_pago = FormCombinado(combinado_svc, self.db_manager, self.assistant_page)
```

---

## Scripts de inicialización (one-shot)

| Script | Propósito | Cuándo ejecutar |
|---|---|---|
| `scripts/seed_members.py` | Inserta los 54 socios fundadores | Una vez, en DB nueva |
| `scripts/seed_historical_credits.py` | Inserta créditos históricos | Una vez, en DB nueva |

Estos scripts no son parte del flujo normal de la app. Se ejecutan manualmente
antes del primer uso en producción.

---

## Notas de despliegue

- **Desarrollo:** correr `python app.py` desde la raíz del proyecto.
- **Producción:** empaquetar con `python build.py` (PyInstaller). El ejecutable
  busca `Archivos_BGC/` en la misma carpeta donde está el `.exe`.
- La app **no requiere instalación de Python** en producción (todo viene empaquetado).
- Dependencias: `PySide6`, `openpyxl`, `python-dateutil`.
