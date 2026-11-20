# Publicar y editar el perfil de gpazop

## Publicar en GitHub

1. Crea el repositorio público `gpazop/gpazop`.
2. Sube el contenido de esta carpeta a la raíz, incluido `README.md`. Desde Git, confirma que la carpeta oculta `.github` forma parte del commit.
3. Abre tu [perfil](https://github.com/gpazop) para ver el README. La guía de GitHub detalla los [requisitos del perfil](https://docs.github.com/en/account-and-profile/how-tos/profile-customization/managing-your-profile-readme).

## Destinos de los paneles

En `README.md`, cambia el valor de `href` del enlace que envuelve cada imagen. El encabezado y la tarjeta **Portafolio** comparten el destino actual. Si publicas otra web, actualiza ambos. **Formación** lleva a la sección del README y puede apuntar a tu página de credenciales cuando la tengas. **Repositorios** y cada proyecto destacado se pueden actualizar de la misma manera.

## Tarjetas y animaciones

`scripts/render.py` contiene los textos y colores de las tarjetas. El retrato está en `scripts/retrato.png` y se incrusta en las dos versiones de la portada. Para regenerar todas las tarjetas, ejecuta `python scripts/render.py` desde la raíz. Se usa la biblioteca estándar de Python 3.10 o posterior.

El nombre de la portada usa los contornos de [Instrument Serif](https://github.com/google/fonts/tree/main/ofl/instrumentserif) guardados en `scripts/nombre-instrument-serif.json`. Por eso se puede ver con la misma tipografía en cualquier navegador. El archivo `scripts/Instrument-Serif-OFL.txt` contiene la licencia.

El usuario de la portada usa los contornos de [Geist Mono](https://github.com/vercel/geist-font) guardados en `scripts/usuario-geist-mono.path`. La licencia está en `scripts/Geist-Mono-OFL.txt`.

Una vez publicado el flujo en la rama predeterminada, **Actualizar actividad del perfil** se programa a diario a las 6:23 a. m. de Lima (11:23 UTC). Lee el calendario de GitHub como visitante, sin credenciales personales. La tarjeta `cards/actividad.svg` muestra la actividad por día. La tarjeta `cards/contribuciones.svg` suma las contribuciones por mes y recalcula la mejor racha, los días activos y el día de mayor actividad.

Puedes iniciarlo también desde **Actions → Actualizar actividad del perfil → Run workflow**. El flujo guarda las tarjetas cuando cambian. Si cambia el formato del calendario o la descarga falla, conserva las tarjetas anteriores. Las animaciones respetan la preferencia de movimiento reducido.

Las tarjetas de actividad incrustan Instrument Serif y Geist Mono desde `scripts/fonts/`. El gráfico mensual abarca los últimos doce meses del calendario, incluido el mes actual hasta la última fecha disponible.
