# 04 — Entorno: producción y pruebas

Cómo cambiar la app entre la base **real** y la de **pruebas**, y cómo saber de
un vistazo en cuál se está.

> La explicación completa del sistema —incluyendo la API y el bot, y lo que
> falta configurar en Railway y Fly.io— está en el repo `bgc-platform`, en
> `docs/12-entornos-produccion-y-pruebas.md`. Este documento cubre solo la app
> de escritorio.

---

## Las dos bases

Son idénticas en estructura y datos. Se distinguen **solo por el puerto**:

| Entorno | Puerto |
|---|---|
| Producción | **42792** |
| Pruebas | **54722** |

Que se parezcan tanto es el riesgo: equivocarse de URL no produce ningún error,
simplemente se escribe donde no era.

---

## Cómo cambiar de entorno

Editar **dos líneas** del `.env` (el que está junto al `.exe`, o en la raíz del
repo en desarrollo):

```ini
# --- Para trabajar en PRUEBAS ---
APP_ENV=pruebas
DATABASE_URL=postgresql://postgres:<pass>@sakura.proxy.rlwy.net:54722/railway
```

```ini
# --- Para volver a PRODUCCIÓN ---
APP_ENV=produccion
DATABASE_URL=postgresql://postgres:<pass>@sakura.proxy.rlwy.net:42792/railway
```

**Hay que cambiar las dos.** `APP_ENV` manda sobre cualquier otra pista, así que
si queda en `pruebas` con la `DATABASE_URL` de producción, la app mostrará el
aviso de pruebas **mientras escribe en la base real**.

Después de editar el `.env`, cerrar y volver a abrir la app.

---

## Cómo se nota

En **producción** la app se ve exactamente igual que siempre — ningún cambio.

En **pruebas**:

- Franja **ámbar permanente** bajo la barra superior, sin botón de cerrar:
  `🧪 MODO PRUEBAS — los cambios NO afectan la base real · host:puerto/base`
- El título de la ventana pasa a `bgc software vX.Y.Z — 🧪 PRUEBAS`.
- Al arrancar, la consola imprime `🌐 Entorno: PRUEBAS · host:puerto/base`.

Si se abren las dos a la vez, el título permite distinguirlas en la barra de
tareas.

---

## Si `APP_ENV` no está definida

La app deduce el entorno del puerto de la `DATABASE_URL`. Y si tampoco lo
reconoce, **asume producción**.

Es a propósito: creer que se está en pruebas cuando en realidad se está
moviendo plata real es el error caro. Ante la duda, la app se comporta como si
fuera la base real.

---

## Dónde está el código

`entorno.py`, en la raíz del repo. No importa Qt, así que también se puede usar
desde scripts de mantenimiento:

```python
import entorno

entorno.es_produccion()          # True / False
entorno.es_pruebas()
entorno.etiqueta()               # 'PRODUCCIÓN' | 'PRUEBAS'
entorno.descripcion_conexion()   # 'host:puerto/base' — nunca la contraseña
entorno.resumen()                # 'PRUEBAS · host:puerto/base'
```

Es buena costumbre empezar cualquier script que escriba en la base con:

```python
assert entorno.es_pruebas(), "Esto no debe correr contra producción"
```

La franja visual vive en `views/widgets/env_banner.py` y se monta en
`views/main_window.py`.
