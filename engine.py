"""Batch downloads; no GUI calls from worker threads."""
import os, sys, subprocess, threading, re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from core import format_options
from runtime import downloader_command
FLAGS = subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0

class Batch:
    def __init__(self, emit, popen=subprocess.Popen):
        self.emit=emit; self.popen=popen; self.cancelled=threading.Event()
        self.lock=threading.Lock();self.processes={}
    def cancel(self):
        with self.lock:
            self.cancelled.set()
            # Hold lock until termination request: prevents a stale PID being reused.
            for proc in list(self.processes.values()):
                if proc.poll() is None:
                    if os.name=='nt':
                        subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=FLAGS,timeout=15)
                    else:proc.terminate()
    def run(self, urls, folder, kind, quality, node, ffmpeg, workers=3):
        try:
            with ThreadPoolExecutor(max_workers=max(1,min(3,workers))) as pool:
                futures=[pool.submit(self.one,i,u,folder,kind,quality,node,ffmpeg) for i,u in enumerate(urls)]
                for f in futures: f.result()
        finally:self.emit(('batch_done',None,None))
    def one(self,i,url,folder,kind,quality,node,ffmpeg):
        proc=None;code=1
        command=downloader_command()+['--ignore-config','--no-playlist','--no-colors','--newline','--encoding','utf-8','--windows-filenames','--no-overwrites','--socket-timeout','15','--retries','2','--fragment-retries','2','--concurrent-fragments','4','--progress-delta','0.5','--js-runtimes','node:'+node,'--ffmpeg-location',ffmpeg,'--match-filters','!is_live','--progress-template','download:VAO_PROGRESS:%(progress._percent_str)s','--print','before_dl:VAO_TITLE:%(title)s','--print','after_move:VAO_FILE:%(filepath)s','--no-simulate','-o',str(Path(folder)/'%(title).140s [%(id)s].%(ext)s')]+format_options(kind,quality)+['--',url]
        try:
            with self.lock:
                if self.cancelled.is_set():self.emit(('done',i,'Cancelado'));return
                proc=self.popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,encoding='utf-8',errors='replace',creationflags=FLAGS)
                self.processes[i]=proc
            self.emit(('state',i,'Conectando…'))
            for line in proc.stdout:
                line=line.rstrip()
                if line.startswith('VAO_PROGRESS:'):
                    match=re.search(r'([\d.]+)%',line)
                    if match:self.emit(('progress',i,float(match.group(1))/100))
                elif line.startswith('VAO_TITLE:'):self.emit(('title',i,line[10:]))
                elif any(s in line for s in ('[Merger]','[ExtractAudio]','[VideoRemuxer]')):self.emit(('state',i,'Convirtiendo…'))
                if not line.startswith('VAO_PROGRESS:'):self.emit(('log',i,line))
            code=proc.wait()
        except Exception as e:self.emit(('log',i,str(e)))
        finally:
            with self.lock:self.processes.pop(i,None)
        self.emit(('done',i,'Cancelado' if self.cancelled.is_set() else ('Listo' if code==0 else 'Error')))
