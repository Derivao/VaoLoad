"""Build on Windows x64: python build_windows.py. Downloads official tools."""
import hashlib, json, os, platform, shutil, subprocess, sys, urllib.request, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def get(url):
    req=urllib.request.Request(url,headers={'User-Agent':'VaoLoad-build/0.3'})
    with urllib.request.urlopen(req,timeout=120) as response:return response.read()

def verified_download(url, sums, name, destination):
    expected=None
    for line in sums.decode().splitlines():
        parts=line.split()
        if len(parts)>=2 and parts[-1].lstrip('*')==name:expected=parts[0].lower();break
    if expected is None:raise RuntimeError('No hay checksum oficial para '+name)
    data=get(url)
    if hashlib.sha256(data).hexdigest()!=expected:raise RuntimeError('Checksum inválido: '+name)
    destination.write_bytes(data)

def build():
    if sys.platform!='win32' or platform.machine().lower() not in ('amd64','x86_64') or sys.maxsize<2**32:
        raise RuntimeError('Compila con Python x64 en Windows x64.')
    os.chdir(ROOT)
    print('Preparando dependencias...',flush=True)
    subprocess.run([sys.executable,'-m','pip','install','--upgrade','pyinstaller>=6,<7','customtkinter>=5.2,<6','imageio-ffmpeg'],check=True)
    cache=ROOT/'build-tools';cache.mkdir(exist_ok=True)
    # Resolve once, then download all assets from the same immutable release tag.
    release=json.loads(get('https://api.github.com/repos/yt-dlp/yt-dlp/releases/latest'))
    base='https://github.com/yt-dlp/yt-dlp/releases/download/'+release['tag_name']+'/'
    print('Descargando yt-dlp '+release['tag_name'],flush=True)
    verified_download(base+'yt-dlp.exe',get(base+'SHA2-256SUMS'),'yt-dlp.exe',cache/'yt-dlp.exe')
    entries=json.loads(get('https://nodejs.org/dist/index.json'))
    node=next(e for e in entries if e['version'].startswith('v24.') and e.get('lts') and 'win-x64-zip' in e['files'])
    name='node-'+node['version']+'-win-x64.zip';base='https://nodejs.org/dist/'+node['version']+'/'
    print('Descargando Node.js '+node['version'],flush=True)
    verified_download(base+name,get(base+'SHASUMS256.txt'),name,cache/'node.zip')
    with zipfile.ZipFile(cache/'node.zip') as z:
        prefix=name[:-4]+'/'
        (cache/'node.exe').write_bytes(z.read(prefix+'node.exe'))
        (cache/'NODE-LICENSE.txt').write_bytes(z.read(prefix+'LICENSE'))
    import imageio_ffmpeg
    shutil.copy2(imageio_ffmpeg.get_ffmpeg_exe(),cache/'ffmpeg.exe')
    subprocess.run([sys.executable,'-m','unittest','discover','-p','test_*.py'],check=True)
    print('Compilando VaoLoad...',flush=True)
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm','--clean','--onedir','--windowed','--noupx','--name','VaoLoad','--icon',str(ROOT/'vaoload.ico'),'--collect-all','customtkinter','app.py'],check=True)
    target=ROOT/'dist'/'VaoLoad';tools=target/'tools';tools.mkdir(exist_ok=True)
    for name in ['yt-dlp.exe','node.exe','ffmpeg.exe','NODE-LICENSE.txt']:shutil.copy2(cache/name,tools/name)
    (target/'LEEME.txt').write_text('Abre VaoLoad.exe. Conserva las carpetas _internal y tools junto al ejecutable.\nNo requiere instalar Python ni Node.js.\nContenido propio o autorizado.\n',encoding='utf-8')
    (tools/'YT-DLP-LICENSE.txt').write_bytes(get('https://raw.githubusercontent.com/yt-dlp/yt-dlp/'+release['tag_name']+'/LICENSE'))
    # Record tool versions and FFmpeg build configuration for support and licenses.
    records=[]
    for args in [[str(tools/'yt-dlp.exe'),'--version'],[str(tools/'node.exe'),'--version'],[str(tools/'ffmpeg.exe'),'-version']]:
        result=subprocess.run(args,capture_output=True,text=True,errors='replace',check=True)
        records.append(result.stdout+result.stderr)
    (tools/'VERSIONES.txt').write_text('\n'.join(records),encoding='utf-8')
    (tools/'DEPENDENCIAS.txt').write_text('yt-dlp: https://github.com/yt-dlp/yt-dlp\nNode.js: https://nodejs.org\nFFmpeg binario de imageio-ffmpeg: https://github.com/imageio/imageio-ffmpeg\nLicencias/build de FFmpeg: ver VERSIONES.txt y https://ffmpeg.org/legal.html\nInterfaz: CustomTkinter MIT: https://github.com/TomSchimansky/CustomTkinter\n',encoding='utf-8')
    shutil.make_archive(str(ROOT/'VaoLoad-App-Windows'),'zip',ROOT/'dist','VaoLoad')
    print('LISTO: VaoLoad-App-Windows.zip',flush=True)
if __name__=='__main__':build()
