import sys, shutil
from pathlib import Path

def tool_path(name):
    if getattr(sys,'frozen',False):
        path=Path(sys.executable).parent/'tools'/name
        if not path.is_file():raise FileNotFoundError(f'Falta tools/{name}. Extrae toda la carpeta de VaoLoad.')
        return str(path)
    return None

def downloader_command():
    bundled=tool_path('yt-dlp.exe')
    return [bundled] if bundled else [sys.executable,'-m','yt_dlp']

def dependencies():
    if getattr(sys,'frozen',False):return tool_path('node.exe'),tool_path('ffmpeg.exe')
    import imageio_ffmpeg
    node=shutil.which('node')
    if not node:raise ValueError('Instala Node.js LTS desde nodejs.org y vuelve a abrir VaoLoad.')
    return node,imageio_ffmpeg.get_ffmpeg_exe()
