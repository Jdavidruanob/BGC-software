# BGC Software — Guía técnica para agentes de IA

Este documento es para un agente nuevo que necesita entender el código rápidamente.
No explica qué hace la app (eso está en `SPEC.md`), sino **cómo está estructurado
el código, cómo fluye la información, y qué reglas hay que respetar**.

---

## Punto de entrada

```
python app.py
```

`app.py` (~120 líneas) es el único lugar donde se instancian y conectan todas las
dependencias. Si quieres entender quién recibe qué, empieza ahí.

---

## Arquitectura en 4 capas

```
Views  →  Services  →  Repositories  →  DBConnection
```

| Capa | Carpeta | Regla principal |
|---|---|---|
| Views | `views/`, `views/widgets/forms/` | Sin SQL, sin lógica de negocio |
| Services | `services/` | Un `commit()` por operación pública |
| Repositories | `db/repositories/` | Solo CRUD, nunca `commit()` |
| Conexión | `db/connection.py` | `sqlite3.connect` + `row_factory=sqlite3.Row` |

La fachada `db/db_manager.py` es un wrapper de los repos usado **solo por las vistas
de lectura** (`members_page`, `member_detail_page`, `assistant_page`, `liquidation_page`).
Los servicios NO dependen de `db_manager`.

---

## Cómo fluye una operación de escritura

Ejemplo: registrar un aporte.

```
FormAporte.submit()
  └─▶ self._service.register(recibi_de_id, recibi_data, aportes, count_cobrables)
        ├─ cursor = self._db.conn.cursor()     ← DBConnection
        ├─ cursor.execute(INSERT recibos ...)
        ├─ cursor.execute(UPDATE socios ...)
        ├─ self._config.set("saldo_en_caja", ...)   ← ConfigRepository
        ├─ self._auxiliar.add(...)                   ← AuxiliarRepository
        ├─ self._db.conn.commit()
        └─ generar_recibo_solo_aportes(...)
              └─▶ returns excel_path
      returns (recibo_id, excel_path)
  └─▶ show_success(...)
  └─▶ self.operation_registered.emit()   ← Signal Qt para refrescar resumen
```

**Nunca** hay SQL fuera de repositorios y servicios. Los forms solo llaman al
servicio y muestran el resultado.

---

## Inyección de dependencias

No hay framework de DI. Todo es wiring manual en `app.py`.

Los **servicios** reciben en su constructor exactamente los repos que necesitan:

```python
# Constructores actuales
AporteService(db: DBConnection, config: ConfigRepository, auxiliar: AuxiliarRepository)
RetiroService(db, config, auxiliar)
CreditoService(db, creditos: CreditosRepository, auxiliar, config)
PagoService(db, liquidaciones: LiquidacionesRepository, auxiliar, config)
CombinadoService(db, liquidaciones, auxiliar, config)
CajaService(config, auxiliar)          # ← no necesita DBConnection
```

Los **forms** reciben el servicio ya construido (llega desde `HomePage`):

```python
# Patrón de constructor en todos los forms
def __init__(self, service, db_manager, ...):
    self._service = service   # pre-construido
    self.db = db_manager      # solo para lecturas (get_all_members_full, etc.)
```

---

## Transacciones — regla crítica

- **Repositorios**: ejecutan SQL con cursor pero **nunca** llaman a `commit()` ni `rollback()`.
- **Servicios**: abren una transacción implícita, hacen toda la operación en un `try / except`, y llaman a `commit()` al final o `rollback()` en el `except`.
- Todo dentro de un mismo servicio comparte la misma conexión y por tanto la misma transacción.

```python
# Patrón estándar en servicios
cursor = self._db.conn.cursor()
try:
    cursor.execute(...)
    self._repo.some_method(...)   # también usa self._db.conn internamente
    self._db.conn.commit()
    excel_path = generar_recibo_(...)
    return resultado
except Exception:
    self._db.conn.rollback()
    raise
```

---

## Generadores de Excel

Los generadores en `utils/recibo_generator_*.py` **no tienen acceso a la DB**.
Cuando necesitan consultar la DB (p.ej. total de cuotas de un crédito), reciben
un **callable** como parámetro:

```python
# Firma actual de los generadores de pago y combinado
def generar_recibo_solo_pagos(get_total_cuotas, recibo_id, recibi_de_data, ...):
    # dentro del generador:
    total = get_total_cuotas(letra_id)   # llama al repo

# En el servicio:
generar_recibo_solo_pagos(
    get_total_cuotas=self._liquidaciones.get_total_cuotas,
    ...
)
```

Las plantillas `.xlsx` tienen columnas fijas — **no modificar su estructura**.
Solo se rellenan valores en celdas específicas.

---

## Invariantes financieros

Estas reglas están en el código y no deben romperse nunca:

| Invariante | Dónde se aplica |
|---|---|
| `mora → total_admin`, nunca a `saldo_en_caja` | `pago_service.py`, `combinado_service.py` |
| `papelería ($3.000/aporte cobrable) → total_admin` | `aporte_service.py`, `combinado_service.py` |
| `saldo_en_caja` refleja el efectivo real | Toda operación que mueve caja |
| Mora: período de gracia de 1 mes | `services/amortization.py → calculate_mora` |
| Commit de caja y auxiliar en la misma transacción | Todos los servicios de escritura |

---

## Errores de negocio

Los servicios lanzan `ValueError` con mensaje en español cuando hay un error de
validación (saldo insuficiente, abono incompleto, etc.). Los forms los capturan:

```python
try:
    recibo_id, excel_path = self._service.register(...)
    show_success(self, "Éxito", "Operación registrada.")
except ValueError as e:
    show_error(self, "Error", str(e))
```

No hay manejo de errores de DB en vistas — si el repo lanza una excepción no
esperada, el servicio hace rollback y la re-lanza; la vista la muestra con `show_error`.

---

## Estilos QSS

```python
# Para cargar estilos en cualquier widget:
from config import load_styles, STYLES_DIR
load_styles(self, os.path.join(STYLES_DIR, "mi_componente.qss"))
```

`load_styles` siempre carga `shared.qss` primero y luego el QSS del componente,
con interpolación `%(VARIABLE)s` de las constantes de color definidas en `config.py`.

---

## Cómo agregar una nueva operación

1. **Repositorio** (si se accede a una tabla nueva): añadir método al repo existente
   o crear uno nuevo en `db/repositories/`.
2. **Servicio**: crear o extender un servicio en `services/`. El constructor recibe
   los repos que necesita. Un solo `commit()` al final.
3. **Generador Excel** (si aplica): en `utils/`. Recibe datos ya procesados, sin DB.
   Si necesita un dato del repo, recibirlo como callable.
4. **Form**: el constructor recibe el servicio. Solo recolecta input → llama al
   servicio → muestra resultado.
5. **Wiring en `app.py`**: construir el servicio inyectando sus repos desde `db_manager`.
6. **Pasar el servicio por la cadena**: `app.py` → `HomePage` → `Form`.

---

## Archivos clave para orientarse rápido

| Archivo | Por qué leerlo primero |
|---|---|
| `app.py` | Muestra todo el wiring: quién instancia a quién |
| `db/db_manager.py` | Expone los property accessors de repos; entiende qué hay disponible |
| `services/pago_service.py` | El servicio más complejo; patrón de referencia para transacciones |
| `services/amortization.py` | Funciones puras de cálculo; lógica financiera central |
| `db/repositories/liquidaciones_repo.py` | Muestra el patrón de repo con lógica no trivial (`recalculate_amortization`) |
| `config.py` | Constantes globales, rutas, utilidades de fecha y formato |

---

## Lo que NO hacer

- **No hacer `commit()` en repositorios.** Solo en servicios.
- **No poner lógica de negocio en views.** Ni siquiera validaciones simples que dependan de la DB.
- **No instanciar servicios dentro de los forms.** Los servicios llegan inyectados.
- **No agregar métodos de escritura a `db_manager`.** Es solo lectura para vistas.
- **No modificar la estructura de las plantillas `.xlsx`.** Solo se rellenan celdas.
- **No agregar mora a `saldo_en_caja`.** Va siempre a `total_admin`.
- **No hacer múltiples `commit()` en un mismo flujo de operación.** Todo en uno.
