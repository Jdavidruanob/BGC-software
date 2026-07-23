# Qué hay que hacer — App de escritorio BGC

> **Este documento es para el desarrollador (persona).** Explica *qué* se va a
> hacer y por qué, sin código, para que entiendas el alcance y puedas revisar
> que el trabajo quede bien hecho.
>
> **Antes de empezar a codear, tu agente debe leer LOS DOS documentos:**
> 1. Este (`01-QUE-HAY-QUE-HACER.md`) — el *qué* y el *por qué*.
> 2. `02-INSTRUCCIONES-AGENTE.md` — el *cómo*: reglas técnicas, código y calidad.
>
> Cada punto de aquí fue pedido explícitamente por el dueño. No es "mejora general
> y ya": hay detalles con mención especial que **no se pueden saltar**.

---

## 0. El panorama

La cooperativa ya tiene un sistema en la nube funcionando: una **API** y un **bot
de Telegram** que comparten una sola base de datos **PostgreSQL**. Por ahí ya se
registran aportes, pagos, retiros, créditos y recibos.

Hoy la app de escritorio guarda todo en un archivo **SQLite local**. El trabajo
principal es que la app deje de usar ese archivo y trabaje contra la **misma base
de datos en la nube** que el bot. Una sola fuente de verdad: lo que hace la app se
ve en el bot y al revés.

Además de la conexión, hay un rediseño de interfaz y funciones nuevas (POS,
inicio, dashboard). Todo dentro del repo **BGC-software** — no se toca nada de la
plataforma (API/bot); eso lo maneja el otro equipo.

---

## 1. Conectar a la base de datos en la nube

- La app debe **conectarse a PostgreSQL** (la de la nube), no a SQLite local.
- Al terminar, la app maneja **una sola base compartida** con el bot.
- **Importante:** la estructura de la base (las tablas) la administra la API. La
  app **no crea ni modifica tablas**; solo lee y escribe datos sobre lo que ya
  existe. (El agente tiene el detalle técnico y las advertencias en el doc 02.)
- La contraseña de la base se entrega **por canal privado** y va en un archivo de
  entorno, nunca en el código ni en el repositorio.

**Lo que ya hicimos de nuestro lado:** agregamos a la base una columna para
guardar las fotos de los socios dentro de la base (ver punto 4). El agente no
tiene que crearla.

---

## 2. Rediseño de interfaz (UI/UX) — mejora general

La app ya tiene una estética que **se respeta**. Lo que falta es pulir el diseño:
está bien de base pero le falta mucho en UI/UX. Es una tarea general de "que se
vea bien y sea cómodo", con estos criterios:

- **Proporciones y espaciado** parejos; nada apretado ni descuadrado.
- **Convenciones** respetadas (lo positivo en verde, lo de eliminar/cerrar en
  rojo, etc.).
- **Iconos** coherentes en estilo y tamaño.
- **Flechas de "volver"** bien colocadas e **iguales en toda la app** (mismo
  lugar, mismo comportamiento en cada pantalla).
- Que **se vea bien**, ordenado y consistente.

### Es para adultos mayores

El usuario principal es una persona mayor. **Entre más práctico, mejor:**

- **Letra suficientemente grande** y legible.
- Botones grandes, alto contraste.
- Fácil de entender y de manejar; flujos cortos y directos.

---

## 3. Formularios — cambios explícitos (con mención especial)

Estos dos NO son "mejora general", son pedidos concretos:

1. **Estética y practicidad de los formularios.** Mejorar cómo se ven y cómo se
   usan todos los formularios (aporte, pago, retiro, combinado, crédito). Buscar
   alternativas mejores a lo actual.

2. **Selector de socio buscable.** Sobre todo, mejorar la selección de un socio:
   que se pueda **escribir para buscar** el socio en el selector/combobox, en vez
   de recorrer una lista larga. Esto es clave para la comodidad.

3. **Auto-rellenar "Recibí de".** El socio elegido en el campo **"Recibí de"**
   debe colocarse **automáticamente como el primer socio abajo**. Hoy, si el mismo
   que entrega la plata es quien hace el aporte, toca **buscarlo y seleccionarlo
   dos veces** (arriba en "recibí de" y abajo en la operación). Con el cambio: se
   elige una sola vez y ya queda puesto abajo; si es otra persona, se cambia.

---

## 4. Sección de socios → mini POS (rehacer completa)

Hay que **remodelar por completo** la sección de socios y convertirla en un **mini
sistema POS** para manejar la base de datos.

- Debe permitir **ver los socios, su saldo, editarlos y eliminarlos**, y también
  ver/manejar sus **créditos**.
- El diseño actual de **cards con imagen grande** se puede quitar y volverlo más
  tipo POS (lista/tabla práctica). **Pero la imagen no se elimina del todo**: se
  deja presente en alguna parte (por ejemplo una miniatura por fila o al abrir el
  detalle del socio).
- **Las imágenes ahora se guardan en la base de datos**, no como ruta de archivo
  local. (Ya dejamos la columna lista.)
- El sistema debe permitir **bajar los datos de la base en la nube y actualizarlos
  a voluntad**. La app trabaja siempre en línea contra la base compartida.
- Debe ser un sistema **completo y blindado**: poder editar prácticamente
  cualquier cosa con seguridad, sin descuadrar los datos.

### 4.1 Agregar créditos manuales (históricos)

Hay créditos/liquidaciones que el abuelo ya hizo **a mano** en el pasado y que hay
que cargar. Para esto **no sirve** el método clásico de "crear crédito" (ese
calcula la cuota solito). Se necesita una variante que:

- Reciba: el **socio**, el **valor prestado**, el **número de cuotas** y **la
  cuota** de cuánto quedó inicialmente.
- A partir de esa cuota, genere la liquidación (el calendario de pagos).
- Se **basa en el método actual** de crear crédito, pero en vez de calcular la
  cuota, la recibe como dato.

### 4.2 Editar una cuota y que las demás se reajusten

Como los abuelos ajustaron liquidaciones manualmente, el POS debe permitir
**editar el valor de una cuota y que las demás se reajusten** para que el crédito
siga cuadrando (que se pague completo).

**Ejemplo:** un crédito con cuotas de **$430.000**. Se quiere dejar la **última en
$40.000**: entonces las cuotas anteriores se recalculan para que la suma siga
pagando el crédito. Igual si la **primera** queda en **$20.000** y el resto se
ajusta. Estos ajustes pasan porque así los hicieron a mano. El POS debe permitir
hacerlos de forma segura, sin descuadrar el capital.

> Para todo lo que toca plata o liquidaciones, hay que **basarse en los métodos
> que ya existen** en la app. La lógica ya está validada por años de uso; no se
> inventan cálculos nuevos.

---

## 5. Inicio — pagos y notificaciones

Agregar en la pantalla de inicio un apartado útil para el día a día, con lo que el
abuelo necesita ver de un vistazo:

- **Próximos pagos / vencimientos** (cuotas que vencen pronto).
- **Próximos en mora** / cuotas ya vencidas.
- **Pagos recientes** (últimos aportes y pagos registrados).
- Recordatorios y avisos que sean **útiles**.

---

## 6. Apartado de datos — dashboard

Empezar la sección de **datos**: un tablero con **métricas de valor** para la
cooperativa. Propuesta de cómo distribuirlo (de lo más importante arriba, al
detalle abajo):

**Arriba — indicadores clave (una fila):**
- **Saldo en caja** (dinero disponible).
- **Aportes de socios** (suma de saldos).
- **Cartera por cobrar** (capital de créditos que falta pagar).
- **Administración** (papelería + mora acumulada).

**En medio — salud de la cartera:**
- Créditos **al día vs. en mora** (cuántos y cuánto dinero).
- **Recaudo del mes** (aportes + pagos del período).
- Conteos: socios activos y créditos vigentes.

**Abajo — detalle y tendencia:**
- **Próximos vencimientos** (lista corta).
- **Créditos más grandes** / mayores deudores.
- **Tendencia de recaudo** por mes (gráfica simple).

> Los colores de estado (verde = al día, rojo = mora, ámbar = por vencer) son
> *además* del azul de la marca.

---

## 7. Colores (respetar la identidad)

Se respetan los colores de la app:

- **Azul** — color principal (acciones, encabezados).
- **Blanco y negro** — fondo y texto.
- **Verde** — lo positivo (guardar, confirmar, dinero).
- Por **convención**: las **X** de cerrar/eliminar y los errores siempre en
  **rojo**.

---

## 8. Cómo trabajar con tu agente

1. Dale a tu agente **los dos documentos** de esta carpeta y pídele que lea
   **ambos** antes de tocar código:
   - `01-QUE-HAY-QUE-HACER.md` (este) — para saber qué se va a hacer y por qué.
   - `02-INSTRUCCIONES-AGENTE.md` — las reglas técnicas, código y calidad.
2. El agente **solo trabaja dentro de BGC-software**. No toca la plataforma
   (API/bot). pero si que puede leerla para entender cosas. (se recomienda tener el proyecto bgc platfomr actualizado y clonada para que el agente lo pueda leer)
3. Sugerencia de orden: **primero la conexión a Postgres** (desbloquea todo y es
   lo más delicado), verificar que funcione, y luego el rediseño, el POS, el
   inicio y el dashboard.

---

## 9. Checklist para revisar el trabajo (tú, el dev)

- [ ] La app se conecta a la base en la nube; no queda ningún archivo `.db` local.
- [ ] Un cambio hecho en la app se ve al consultar por el bot, y al revés.
- [ ] Las flechas de volver, los iconos y las proporciones son consistentes en
      toda la app.
- [ ] La letra es grande y todo se lee y se usa cómodo (pensado para adulto mayor).
- [ ] En los formularios se puede **escribir para buscar** el socio.
- [ ] Al elegir "Recibí de", ese socio ya queda puesto **abajo** sin repetirlo.
- [ ] La sección de socios es un POS: ver / editar / eliminar socios y créditos,
      con la imagen presente (desde la base).
- [ ] Se pueden **agregar créditos manuales** dando la cuota inicial.
- [ ] Se puede **editar una cuota** y las demás **se reajustan** para que el
      crédito cuadre.
- [ ] El inicio muestra próximos pagos, mora y movimientos recientes.
- [ ] El dashboard muestra los indicadores y la salud de la cartera.
- [ ] Los colores respetan la identidad (azul / blanco-negro / verde; X en rojo).
