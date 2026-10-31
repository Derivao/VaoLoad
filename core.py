import re
from urllib.parse import urlparse, parse_qs

def youtube_url(value):
    u = urlparse(value.strip())
    if u.scheme not in ('http', 'https') or u.username or u.password or u.port:
        raise ValueError('Pega un enlace válido de YouTube.')
    if u.hostname in ('youtu.be', 'www.youtu.be'):
        video = u.path.strip('/').split('/')[0]
    elif u.hostname in ('youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com'):
        match = re.fullmatch(r'/(?:shorts|embed|live)/([\w-]{11})/?', u.path)
        video = parse_qs(u.query).get('v', [''])[0] if u.path == '/watch' else (match.group(1) if match else '')
    else:
        raise ValueError('Por ahora solo se admite YouTube.')
    if not re.fullmatch(r'[\w-]{11}', video):
        raise ValueError('No se encontró un video válido en ese enlace.')
    return 'https://www.youtube.com/watch?v=' + video

def format_options(kind, quality):
    if kind == 'MP3':
        if quality not in ('128', '192', '320'): raise ValueError('Calidad inválida')
        return ['-f', 'bestaudio/best', '-x', '--audio-format', 'mp3', '--audio-quality', quality+'K']
    if kind != 'MP4' or quality not in ('360','480','720','1080','1440','2160'): raise ValueError('Calidad inválida')
    return ['-f', f'bestvideo[height<={quality}][ext=mp4]+bestaudio[ext=m4a]/best[height<={quality}][ext=mp4]', '--merge-output-format', 'mp4']

def batch_urls(text):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines: raise ValueError('Pega al menos un enlace.')
    if len(lines) > 50: raise ValueError('Máximo 50 enlaces por lote.')
    urls=[]
    for i,line in enumerate(lines,1):
        try: url=youtube_url(line)
        except ValueError as e: raise ValueError(f'Línea {i}: {e}') from e
        if url not in urls: urls.append(url)
    return urls
