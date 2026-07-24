# Optimización de rendimiento — app de escritorio BGC

Este documento registra por qué la app se sentía lenta tras migrar a PostgreSQL
en la nube y qué se hizo para acelerarla, para que cualquiera que la mantenga en
el futuro entienda el criterio.

---

## 1. El diagnóstico: la lentitud es latencia de red, no la app

Cuando la base era **SQLite local**, cada consulta tardaba microsegundos (el
archivo estaba en el mismo disco). Al pasar a **PostgreSQL en la nube** (a través
del proxy de Railway), cada consulta es ahora un **viaje de ida y vuelta por red**.

Se midió con la base real:

| Operación | Tiempo |
|---|---|
| `SELECT 1` (latencia pura de red) | **~130–150 ms** |
| Abrir la pestaña **Inicio** | **~1.825 ms** |
| Abrir el **Dashboard** | **~1.455 ms** |

Conclusión clave: **da igual que la consulta sea trivial; cada una cuesta ~130 ms
solo por el viaje.** Por eso lo que hay que reducir es la **cantidad de consultas
en serie**, no "hacer las consultas más rápidas".

Las causas concretas:

- **Inicio** disparaba ~14 consultas cada vez que se entraba, y **5 de ellas eran
  idénticas**: los 5 formularios (aporte, pago, combinado, retiro, nuevo crédito)
  pedían la lista de socios por separado.
- **Dashboard** ejecutaba ~9 consultas escalares una tras otra.
- El **Resumen de Caja** de Inicio hacía 4 consultas por separado.

---

## 2. Qué se hizo

### 2.1 Caché corto de la lista de socios (`db/db_manager.py`)

`get_all_members_full()` / `get_all_members()` se llaman en muchos lugares (los 5
formularios, el POS, el diálogo de crédito manual…). Ahora `DBManager` guarda el
resultado en memoria con una **vida corta de 4 segundos**:

- Dentro de una misma ráfaga de refresco (los 5 formularios cargan en
  milisegundos), las 5 llamadas se sirven de **una sola consulta real**.
- El caché **se invalida** (se fuerza recargar) cuando:
  - se crea, edita o elimina un socio,
  - se crea un crédito manual,
  - se registra cualquier operación (se invalida en `HomePage.refresh_forms`).
- Fuera de eso, a los 4 segundos expira solo. Así nunca queda desactualizado más
  de unos segundos y, tras cualquier cambio, se recarga fresco.

Método nuevo: `DBManager.invalidate_members()`.

### 2.2 Dashboard en una sola consulta (`db/db_manager.py → dashboard_metrics`)

Los 9 indicadores escalares (saldo en caja, aportes, cartera, administración,
mora, socios activos, créditos vigentes, en mora, recaudo del mes) se calculan
ahora en **un único `SELECT`** con subconsultas:

```sql
WITH prox AS (...)
SELECT
  (SELECT ...) AS saldo_caja,
  (SELECT ...) AS aportes_socios,
  ...
  (SELECT ...) AS cartera;
```

La tendencia por mes y los mayores deudores siguen siendo una consulta cada una
(devuelven varias filas). Total: **3 viajes en vez de ~11**.

### 2.3 Resumen de Caja en una sola consulta (`views/home_page.py`)

Las 4 consultas del "Resumen de Caja" (saldo, papelería, mora, conteo de créditos)
se fusionaron en **un solo `SELECT`** con subconsultas.

### 2.4 Indicador de "cargando" (`views/main_window.py`)

Como las consultas bloquean el hilo de la interfaz, al cambiar de pestaña se
muestra un **cursor de espera** y un **badge central "⏳ Cargando…"**. El truco:
se fuerza el repintado con `QApplication.processEvents()` **antes** de lanzar la
consulta que bloquea, para que el indicador sí sea visible. Se oculta al terminar.

Esto no acelera la consulta, pero la app **comunica que está trabajando** y no se
siente "colgada".

---

## 3. Resultado medido

| Operación | Antes | Después | Mejora |
|---|---|---|---|
| **Dashboard** | ~1.455 ms | **~390 ms** | **3,7× más rápido** |
| **Refresco de Inicio** | ~1.825 ms | **~675 ms** | **2,7× más rápido** |

Los datos siguen siendo correctos (se verificó contra la base real).

---

## 4. Reglas para no volver a ralentizarla

- **Cada consulta contra la nube cuesta ~130 ms.** Antes de agregar una consulta
  en un flujo que se ejecuta seguido (refrescos, cambios de vista), pregúntate si
  se puede **combinar** con otra o **cachear**.
- Prefiere **un `SELECT` con subconsultas** a varios `SELECT` sueltos cuando los
  valores se muestran juntos.
- Evita pedir el mismo dato varias veces en la misma pantalla; cárgalo una vez y
  compártelo.
- Si agregas escrituras que cambian saldos/socios, acuérdate de llamar a
  `db_manager.invalidate_members()` para que el caché no quede viejo.

---

## 5. Siguiente nivel (pendiente, opcional)

- **Consultas en un hilo aparte** para que la ventana no se congele durante la
  espera (mejora la fluidez; es un cambio más delicado por la concurrencia con la
  interfaz).
- Combinar "próximos pagos" + "en mora" del inicio en una sola consulta.
