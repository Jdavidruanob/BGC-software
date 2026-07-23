# Instrucciones técnicas — Agente de desarrollo (BGC-software)

> **Lee primero `01-QUE-HAY-QUE-HACER.md`** para entender el alcance y el *por qué*
> de cada tarea. Este documento es el *cómo*: reglas duras, código concreto y
> estándares de calidad. Ambos documentos son obligatorios.
>
> **Trabajas únicamente dentro del repo `BGC-software`.** No modificas la
> plataforma (API / bot). Cuando dudes de una consulta SQL contra Postgres, la
> referencia probada está en el repo de la plataforma:
> `packages/core/src/coop_core/repositories/` (mismos esquemas, mismas tablas, ya
> escritos para Postgres).

---

## Reglas de trabajo, commits y autoría (obligatorias)

- **Crea una rama nueva desde `main`** y trabaja **todo** ahí (toda la migración,
  el rediseño, el POS, el inicio y el dashboard). No trabajes directo sobre
  `main`.
- **No hagas merge.** Cuando termines, **no fusiones** la rama a `main`: solo
  **avisa que ya terminaste**. El dueño revisa y, si aprueba todo, él mismo hace
  el merge.
- **Nunca** te agregues como colaborador del repositorio, ni te configures como
  autor o co-autor de los commits. Los commits salen **solo a nombre del dueño**.
- **No** agregues trailers tipo `Co-Authored-By: Claude ...` ni ninguna otra
  atribución de co-autoría.
- **No** menciones que el trabajo fue "generado por IA", "hecho con Claude" ni
  nada similar en los mensajes de commit, PRs, comentarios de código ni en el
  repositorio.
- Los mensajes de commit describen el cambio y nada más.

---

## 0. Orden de trabajo recomendado

1. **Migración a PostgreSQL** (bloquea todo lo demás; lo más delicado).
2. Verificar conexión de doble vía con el bot.
3. Fotos en la base (columna ya existente).
4. Rediseño UI/UX + formularios (combobox buscable, auto "Recibí de").
5. POS de socios/créditos (CRUD, crédito manual, edición de cuotas con reajuste).
6. Inicio (próximos pagos, mora, movimientos).
7. Dashboard de datos.

Haz commits pequeños y verificables por área. No mezcles la migración con el
rediseño en un mismo commit.

---

## 1. REGLA DE ORO: la base la administra la API

La estructura de la base (tablas y columnas) la crea y mantiene la API. La app se
conecta a algo que **ya existe**.

### ❌ Prohibido contra la base compartida
- Ejecutar `create_tables()` / `initialize_config_values()` — pueden **borrar
  `saldo_en_caja` y la config real**.
- `ALTER TABLE`, `DROP TABLE`, recrear tablas.
- La "migración anual" que copiaba el `.db` a un archivo nuevo por año — ese
  concepto ya no aplica con una base única compartida. Desactívala.

### ✅ Permitido
- Conectarse, **leer y escribir datos** sobre las tablas existentes.

### ¿Necesitas una columna nueva?
Se pide al equipo de la plataforma para que la agregue en la API. **No la crees
desde el desktop.** (La columna de fotos ya fue agregada — sección 3.)

### En el arranque
La app hoy, al conectar, llama a `create_tables()` e `initialize_config_values()`.
**Sáltate esos pasos** contra la base compartida. Asume que las tablas y la config
ya existen.

---

## 2. Migración SQLite → PostgreSQL

Cuatro cambios mecánicos. La lógica de negocio **no cambia**.

### 2.1 Cadena de conexión por variable de entorno

Nunca hardcodear la URL. Va en un `.env` (agregar `.env` al `.gitignore`).

```
# .env  (el valor real con contraseña lo entrega el dueño por canal privado)
DATABASE_URL=postgresql://postgres:<password>@sakura.proxy.rlwy.net:42792/railway
```

Cargar con `os.environ["DATABASE_URL"]` (o `python-dotenv`).

### 2.2 Conector: `sqlite3` → `psycopg` (v3)

Un solo archivo: `db/connection.py`. Usar `dict_row` para que las filas se
accedan por nombre (`row["saldo"]`) y se conviertan con `dict(row)`, igual que
`sqlite3.Row`.

```python
# ANTES
import sqlite3
self.conn = sqlite3.connect(self.db_path)
self.conn.row_factory = sqlite3.Row

# DESPUÉS
import os, psycopg
from psycopg.rows import dict_row
self.conn = psycopg.connect(os.environ["DATABASE_URL"], row_factory=dict_row)
```

Agregar `psycopg[binary]>=3.1` a `requirements.txt` (y quitar la dependencia de
SQLite si aplica).

### 2.3 Marcadores de parámetros: `?` → `%s`

Hay **~104** repartidos en `db/repositories/`, `views/`, `services/` y `utils/`.
Reemplazo cuidadoso (no tocar `?` que estén dentro de texto de UI).

```python
cursor.execute("SELECT saldo FROM socios WHERE id = ?",  (socio_id,))   # antes
cursor.execute("SELECT saldo FROM socios WHERE id = %s", (socio_id,))    # después
```

### 2.4 IDs de inserción: `lastrowid` → `RETURNING`

Postgres no tiene `lastrowid` (**8 usos**). Pedir el id en el mismo INSERT.

```python
# ANTES
cursor.execute("INSERT INTO socios (...) VALUES (?, ?)", (a, b))
new_id = cursor.lastrowid

# DESPUÉS
cursor.execute("INSERT INTO socios (...) VALUES (%s, %s) RETURNING id", (a, b))
new_id = cursor.fetchone()["id"]
```

### 2.5 SQL específico de SQLite → Postgres

| SQLite | Postgres |
|---|---|
| `DATE('now')` | `CURRENT_DATE` (o pasar la fecha como parámetro Python) |
| `GROUP_CONCAT(x, ', ')` | `STRING_AGG(x, ', ')` |
| `INSERT OR IGNORE` | `INSERT ... ON CONFLICT DO NOTHING` |
| `INSERT OR REPLACE` | `INSERT ... ON CONFLICT (...) DO UPDATE SET ...` |
| `AUTOINCREMENT` | (no aplica — no se crean tablas) |

Buscar también: concatenación con `||` (compatible), `strftime` (usar el
equivalente de Postgres o formatear en Python), y comparaciones de fecha sobre
columnas `TEXT` con formato `YYYY-MM-DD` (siguen funcionando como texto).

### 2.6 Transacciones (`commit` / `rollback`)

`psycopg` **no** hace autocommit por defecto.

- Después de cada operación de escritura: `conn.commit()`.
- Si algo falla en medio de una operación con varios INSERT/UPDATE:
  `conn.rollback()`.
- Envolver las operaciones compuestas (aporte, pago, combinado, crear crédito) en
  una sola transacción: o se guarda todo, o no se guarda nada. Revisar que no
  queden estados a medias (ej: recibo creado sin su detalle, o saldo movido sin
  recibo).

### 2.7 Concurrencia

El bot y la app pueden escribir a la vez. Para 2-3 usuarios el riesgo es bajo,
pero **no leas-modifiques-escribas** `saldo_en_caja` con lógica de aplicación
suelta si puedes evitarlo. Preferir updates atómicos donde tenga sentido
(`UPDATE ... SET saldo = saldo + %s`). Reusar los servicios existentes, que ya
manejan esto.

### 2.8 Verificación de la migración

- La app abre y lista socios reales de la nube con sus saldos.
- Editar un dato en la app → se ve al consultarlo por el bot; y un cambio del bot
  se ve en la app.
- No se crea ningún `.db` nuevo.
- Registrar un aporte desde la app mueve `saldo_en_caja` y `total_admin`
  correctamente.

---

## 3. Fotos de socios en la base

Ya existe la columna `socios.foto` de tipo **`BYTEA`** (bytes de la imagen). No
hay que crearla.

- **Guardar:** leer el archivo elegido como bytes → `UPDATE socios SET foto = %s
  WHERE id = %s` (pasar los bytes; con psycopg se envían como `bytes`).
- **Leer:** `SELECT foto FROM socios WHERE id = %s` → pintar en memoria (QPixmap
  desde bytes), sin escribir a disco.
- **Optimizar:** redimensionar/comprimir antes de guardar (p. ej. máx. 400×400,
  JPEG/PNG) para no inflar la base.
- `photo_path` queda solo por compatibilidad con datos viejos; lo nuevo va a
  `foto`.

---

## 4. UI/UX y formularios

Respetar la estética existente; pulir consistencia y practicidad. (Detalles del
*qué* en el doc 01, secciones 2 y 3.)

### Estándares transversales
- **Componente único de "volver"**: un solo widget reutilizable, mismo ícono,
  misma posición, mismo comportamiento en todas las pantallas. Nada de flechas
  distintas por vista.
- Escala de tamaños de fuente definida y aplicada de forma consistente; base
  grande para adulto mayor.
- Íconos de una sola familia/estilo y tamaños coherentes.
- Espaciado y alineación por layout (no márgenes sueltos que se pisen).
- Estados de foco visibles (teclado) y contraste alto.

### Combobox de socio buscable
- Reemplazar el selector actual por uno con **filtrado por texto** (escribir para
  buscar por nombre). En Qt: `QComboBox` con `setEditable(True)` +
  `QCompleter` con `CaseInsensitive` y coincidencia por contención, o un
  `QLineEdit` + lista filtrada.
- El filtrado debe ser tolerante (ignorar mayúsculas/tildes) y rápido con la
  lista completa de socios.

### Auto "Recibí de" → primer socio de la operación
- Al elegir el socio en **"Recibí de"**, colocarlo automáticamente como el
  **primer ítem** de la lista de la operación (aporte/pago/combinado), sin que el
  usuario tenga que volver a buscarlo.
- Debe seguir siendo editable: si la operación es para otra persona, se puede
  cambiar ese primer ítem.
- Un solo punto de verdad: cambiar "Recibí de" actualiza el primer ítem si aún no
  fue tocado manualmente.

---

## 5. POS de socios y créditos

Rehacer la sección de socios como un POS de administración. (El *qué* está en el
doc 01, sección 4.)

### Vista y CRUD
- Vista tipo lista/tabla: nombre, saldo, acciones (editar, eliminar, ver
  créditos). Búsqueda y orden por nombre/saldo.
- Conservar la imagen **presente pero pequeña** (miniatura por fila o en el
  detalle), cargada desde `socios.foto`.
- CRUD completo y **blindado**: validar antes de escribir, confirmar acciones
  destructivas (eliminar), y usar transacciones.
- Eliminar un socio debe considerar sus dependencias (créditos, recibos): decidir
  entre bloquear la eliminación si tiene historial, o manejarla con cuidado. **No
  dejar la base en estado inconsistente.**

### 5.1 Crear crédito manual (histórico)

Variante del "crear crédito" clásico. En vez de calcular la cuota, **la recibe**.

- Entradas: `socio(s)`, `valor_prestado` (capital), `n_cuotas`, `cuota_inicial`.
- Generar la tabla de amortización a partir de la cuota dada:
  - Base: el método actual de amortización de la app
    (`utils/credit_liquidation_generator.py` / `services`), que hoy calcula la
    cuota. Aquí se usa la cuota como dato de entrada.
  - Regla de cierre: la suma de las cuotas debe pagar el capital completo. La
    **última cuota absorbe el residuo** (capital − cuota_base × (n_cuotas − 1)),
    igual que hace el generador actual con su "cuota final".
  - Interés: mantener el mismo criterio del crédito clásico (interés sobre saldo
    de capital), salvo que el flujo histórico indique otra cosa.
- Escribir las cuotas en `liquidaciones` con la misma forma que el crédito normal
  (para que consultas, pagos y liquidación actual sigan funcionando).

### 5.2 Editar una cuota con reajuste del resto

Permitir cambiar el valor de una cuota y **recalcular las demás** para que el
crédito siga cuadrando (pagar el capital completo).

- Ejemplos reales: cuotas de $430.000 y la **última** en $40.000 → recalcular las
  anteriores; o la **primera** en $20.000 y el resto se ajusta.
- Enfoque sugerido:
  - El usuario fija el valor de una o varias cuotas ("ancladas").
  - Se distribuye el capital restante entre las cuotas **no ancladas** (parejo, o
    con la última absorbiendo el residuo, según lo que se defina en la UI).
  - Recalcular el `saldo_capital` fila por fila para que quede consistente y
    llegue a cero al final.
- **Invariante que no se puede romper:** la suma de capital de todas las cuotas =
  capital del crédito. Validar esto antes de guardar; si no cuadra, no guardar y
  avisar.
- Basarse en la lógica existente de amortización/recálculo (`liquidaciones_repo`
  tiene `recalculate_amortization` en la plataforma como referencia).
- Respetar cuotas ya **pagadas** (`fecha_pago` no nulo): normalmente no se
  reajustan; el recálculo aplica sobre las pendientes.

---

## 6. Inicio: próximos pagos, mora y movimientos

- **Próximos vencimientos:** `liquidaciones` con `fecha_pago IS NULL` y
  `fecha_vencimiento` cercana (ordenar por fecha). Unir con socio/crédito.
- **En mora:** cuotas con `fecha_pago IS NULL` y `fecha_vencimiento` ya pasada
  (usar la fecha del sistema).
- **Movimientos recientes:** últimos registros de `detalle_recibo` / `auxiliar`
  (aportes, pagos, retiros) ordenados por fecha.
- Presentar como tarjetas/listas cortas y legibles en el inicio.

---

## 7. Dashboard de datos

Distribución (detalle en doc 01, sección 6). Fuentes de datos:

- **Saldo en caja:** `config` clave `saldo_en_caja`.
- **Aportes de socios:** `SELECT SUM(saldo) FROM socios`.
- **Cartera por cobrar:** suma de `saldo_capital` de la última cuota pendiente por
  crédito (o el saldo vivo según la lógica de la app).
- **Administración:** papelería (`config.total_admin`) + mora acumulada
  (`SELECT COALESCE(SUM(abono_mora),0) FROM detalle_recibo`).
- **Al día vs. mora:** contar créditos con/ sin cuotas vencidas.
- **Recaudo del mes:** aportes + pagos del período (desde `detalle_recibo` /
  `auxiliar`).
- **Tendencia:** agrupar recaudo por mes.

Para gráficas usar lo que ya use la app (o `QtCharts`/`matplotlib` embebido);
mantenerlas simples y legibles. Colores de estado (verde/rojo/ámbar) **además**
del azul de la marca.

---

## 8. Estándares de calidad (definición de "hecho")

- **Reusar antes que reescribir.** La lógica de plata/liquidaciones ya está
  validada; apóyate en los servicios/repos existentes. No inventar cálculos.
- **Nada de credenciales en el repo.** `DATABASE_URL` por entorno; `.env` en
  `.gitignore`.
- **Transacciones correctas.** Commit al terminar, rollback ante error, sin
  estados a medias.
- **No romper invariantes.** Suma de cuotas = capital; `saldo_en_caja` coherente;
  no dejar la base inconsistente al eliminar.
- **Consistencia visual.** Un solo componente de "volver"; íconos y tamaños
  coherentes; colores de la identidad; convenciones (X en rojo, éxito en verde).
- **Pensado para adulto mayor.** Letra grande, alto contraste, flujos cortos.
- **Probar de doble vía** con el bot antes de dar por terminada la migración.
- Confirmar acciones destructivas; mensajes claros ("Guardado", "Eliminado", y
  errores que digan qué pasó y cómo arreglarlo).

---

## 9. Definition of done (resumen ejecutable)

- [ ] Conexión a Postgres por `DATABASE_URL`; sin `.db` local; sin
      `create_tables`/`init_config`/migración anual contra la base compartida.
- [ ] Todos los `?`→`%s`; `lastrowid`→`RETURNING`; SQL de SQLite adaptado; commits
      y rollbacks correctos.
- [ ] Fotos en `socios.foto` (BYTEA); nada de rutas nuevas.
- [ ] Combobox de socio buscable; "Recibí de" auto-coloca el primer socio.
- [ ] POS de socios/créditos: ver/editar/eliminar, imagen presente, blindado.
- [ ] Crear crédito manual (con cuota inicial) genera la liquidación consistente.
- [ ] Editar cuota reajusta el resto manteniendo la suma = capital.
- [ ] Inicio con próximos pagos, mora y movimientos recientes.
- [ ] Dashboard con indicadores y salud de cartera.
- [ ] UI consistente (volver/íconos/proporciones/colores) y pensada para adulto
      mayor.
- [ ] Verificación de doble vía con el bot pasa.
