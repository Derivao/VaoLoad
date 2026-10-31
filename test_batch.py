import unittest, threading, time, tempfile
from core import batch_urls, format_options
from engine import Batch

def links(n):return ['https://www.youtube.com/watch?v='+f'{i:011d}' for i in range(n)]
class Tests(unittest.TestCase):
    def test_50(self):self.assertEqual(len(batch_urls('\n'.join(links(50)))),50)
    def test_limit(self):
        with self.assertRaises(ValueError):batch_urls('\n'.join(links(51)))
    def test_duplicates(self):self.assertEqual(batch_urls('\n'.join(links(1)*3)),links(1))
    def test_invalid_line(self):
        with self.assertRaisesRegex(ValueError,'Línea 2'):batch_urls(links(1)[0]+'\nhttps://example.com')
    def test_formats(self):
        self.assertIn('192K',format_options('MP3','192'))
        self.assertIn('height<=1080',format_options('MP4','1080')[1])
    def test_bounded_parallel_and_failure(self):
        events=[];lock=threading.Lock();active=0;peak=0;count=0;commands=[]
        class Proc:
            def __init__(self,cmd,**kw):
                nonlocal active,peak,count
                with lock:
                    active+=1;peak=max(peak,active);count+=1;self.code=1 if count==2 else 0;commands.append(cmd)
                self.stdout=self.lines()
            def lines(self):
                yield 'VAO_TITLE:Example\n';time.sleep(.005);yield 'VAO_PROGRESS: 42.0%\n'
            def wait(self):
                nonlocal active
                with lock:active-=1
                return self.code
            def poll(self):return None
        batch=Batch(events.append,popen=Proc)
        with tempfile.TemporaryDirectory() as folder:batch.run(links(50),folder,'MP4','1080','node','ffmpeg')
        done=[e for e in events if e[0]=='done']
        self.assertEqual(len(done),50);self.assertEqual(sum(e[2]=='Error' for e in done),1)
        self.assertLessEqual(peak,3);self.assertGreater(peak,1);self.assertEqual(events[-1][0],'batch_done')
        self.assertIn('--concurrent-fragments',commands[0]);self.assertEqual(commands[0][-2],'--')
    def test_cancel_pending(self):
        events=[]
        def forbidden(*args,**kwargs):raise AssertionError('No debe iniciar procesos')
        batch=Batch(events.append,popen=forbidden);batch.cancel()
        batch.run(links(50),'.','MP3','192','node','ffmpeg')
        self.assertEqual(sum(e[0]=='done' and e[2]=='Cancelado' for e in events),50)
if __name__=='__main__':unittest.main()

class PackagingTests(unittest.TestCase):
    def test_frozen_downloader_does_not_relaunch_gui(self):
        import runtime
        from unittest.mock import patch
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            tools=Path(folder)/'tools';tools.mkdir()
            for name in ('node.exe','ffmpeg.exe','yt-dlp.exe'):(tools/name).touch()
            with patch.object(runtime.sys,'frozen',True,create=True), patch.object(runtime.sys,'executable',str(Path(folder)/'VaoLoad.exe')):
                self.assertEqual(runtime.downloader_command(),[str(tools/'yt-dlp.exe')])
                self.assertEqual(runtime.dependencies(),(str(tools/'node.exe'),str(tools/'ffmpeg.exe')))
                (tools/'node.exe').unlink()
                with self.assertRaises(FileNotFoundError):runtime.dependencies()
