# VaoLoad para Windows

Este paquete contiene el proyecto y el flujo de compilación. Todavía no contiene
VaoLoad.exe: se genera al ejecutar el flujo en un equipo Windows de GitHub Actions.

## GitHub Actions

1. Crea un repositorio privado para VaoLoad.
2. Sube el CONTENIDO de esta carpeta a la raíz del repositorio, incluyendo
   `.github/workflows/windows.yml`. No subas la carpeta contenedora como otra capa.
3. Abre Actions, selecciona «Compilar VaoLoad para Windows» y pulsa Run workflow.
4. Cuando termine correctamente, descarga el artefacto VaoLoad-App-Windows.
5. Extrae el artefacto y después VaoLoad-App-Windows.zip.
6. Abre VaoLoad/VaoLoad.exe.

Conserva juntas las carpetas tools y _internal al mover la aplicación.
No requiere instalar Python, Node.js ni FFmpeg en el PC de uso.
Para un acceso directo, clic derecho en VaoLoad.exe > Mostrar más opciones >
Enviar a > Escritorio (crear acceso directo).
La compilación no lleva firma digital comercial. No incluye instalador.

## Funcionamiento de la compilación

Runner Windows x64, Python 3.12 y PyInstaller en modo carpeta sin consola.
Incluye los datos de CustomTkinter y un icono propio.
Descarga yt-dlp desde una versión oficial resuelta una vez y Node.js 24 LTS
portable desde nodejs.org. Comprueba SHA-256 contra sus sumas oficiales.
FFmpeg se obtiene del paquete imageio-ffmpeg de la compilación.
Ejecuta las pruebas y comprueba que las tres herramientas respondan a --version.
La app empaquetada ejecuta tools/yt-dlp.exe; no se relanza a sí misma.

El flujo requiere acceso a Internet. No publica versiones ni crea releases:
solo guarda un artefacto del workflow durante 14 días. No se incluyen credenciales.
En repositorios privados, el consumo de Actions depende de los minutos y límites
de tu cuenta. La app sigue procesando los videos localmente cuando la uses.

## Validación realizada aquí

Sintaxis, siete pruebas de cola y prueba de resolución de herramientas en modo
empaquetado. No se ha ejecutado el runner Windows ni generado un EXE en este entorno.
El primer workflow confirmará que el empaquetado termina correctamente. Después
hay que probar apertura de ventana y una descarga en Windows.
