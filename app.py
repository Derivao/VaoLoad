import os, shutil, subprocess, threading, queue, random, math, time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
import customtkinter as ctk
from core import batch_urls
from engine import Batch, FLAGS
from runtime import dependencies

ctk.set_appearance_mode('dark')
BG='#090d16'; PANEL='#111b2b'; BLUE='#8bc5ff'; MUTED='#8a9db8'; TEXT='#edf5ff'
class App(ctk.CTk):
    def __init__(self):
        super().__init__();self.title('VaoLoad');self.geometry('920x860');self.minsize(800,760);self.configure(fg_color=BG)
        self.events=queue.Queue();self.batch=None;self.busy=False;self.rows={};self.logs=[];self.done=0
        self.folder=Path.home()/'Downloads'/'VaoLoad'
        self.grid_columnconfigure(0,weight=1);self.grid_rowconfigure(4,weight=1)
        self.motion=True;self.particle_job=None;self.last_frame=time.monotonic()
        self.hero=tk.Canvas(self,bg=BG,highlightthickness=0,height=160)
        self.hero.grid(row=0,column=0,sticky='ew',padx=24,pady=(12,8))
        self.particles=[]
        rng=random.Random(37)
        for _ in range(65):
            x,y=rng.random(),rng.random();r=rng.choice([1,1,1.5,2])
            glow=self.hero.create_oval(0,0,0,0,fill='#101e33',outline='')
            dot=self.hero.create_oval(0,0,0,0,fill=rng.choice(['#263e5c','#436991','#73a9d2']),outline='')
            self.particles.append([x,y,r,rng.uniform(.025,.065),rng.uniform(0,6.28),dot,glow])
        self.hero.create_text(22,38,text='↓',fill=BLUE,font=('Segoe UI',30,'bold'),anchor='w')
        self.hero.create_text(66,38,text='VaoLoad',fill=TEXT,font=('Segoe UI',30,'bold'),anchor='w')
        self.hero.create_text(24,90,text='YouTube, a tu ritmo.',fill=TEXT,font=('Segoe UI',19),anchor='w')
        self.hero.create_text(25,122,text='MP4 / MP3   ·   Hasta 50 enlaces',fill=MUTED,font=('Segoe UI',11),anchor='w')
        self.folderbutton=ctk.CTkButton(self.hero,text='Carpeta ↗',width=116,height=36,command=self.pick,fg_color=PANEL,hover_color='#243650',corner_radius=12,border_width=1,border_color='#24334a')
        self.folder_window=self.hero.create_window(0,36,window=self.folderbutton,anchor='e')
        self.motionbutton=ctk.CTkButton(self.hero,text='Partículas: sí',width=116,height=28,command=self.toggle_motion,fg_color=BG,hover_color=PANEL,text_color=MUTED,corner_radius=10)
        self.motion_window=self.hero.create_window(0,78,window=self.motionbutton,anchor='e')
        self.hero.bind('<Configure>',self.hero_resize)
        self.animate_particles()
        inputbox=ctk.CTkFrame(self,fg_color=PANEL,corner_radius=22,border_width=1,border_color='#233149');inputbox.grid(row=1,column=0,sticky='ew',padx=32)
        bar=ctk.CTkFrame(inputbox,fg_color='transparent');bar.pack(fill='x',padx=18,pady=(14,6))
        ctk.CTkLabel(bar,text='Pega tus enlaces',font=('Segoe UI',15,'bold')).pack(side='left')
        self.counter=ctk.CTkLabel(bar,text='0 / 50',text_color=MUTED);self.counter.pack(side='right')
        self.pastebutton=ctk.CTkButton(bar,text='Pegar',width=65,height=28,command=self.paste,fg_color='#243650',corner_radius=8);self.pastebutton.pack(side='right',padx=12)
        self.links=ctk.CTkTextbox(inputbox,height=145,fg_color='#0c1421',corner_radius=12,border_width=1,border_color='#1b2a40',text_color=TEXT,font=('Segoe UI',13),wrap='none');self.links.pack(fill='x',padx=12,pady=(0,12));self.links.bind('<KeyRelease>',self.count)
        options=ctk.CTkFrame(self,fg_color='transparent');options.grid(row=2,column=0,sticky='ew',padx=32,pady=20)
        self.fmt=ctk.CTkSegmentedButton(options,values=['MP4','MP3'],command=self.change_format,height=44,width=200,corner_radius=14,selected_color='#346397',selected_hover_color='#456fa7',unselected_color=PANEL,unselected_hover_color='#243650',font=('Segoe UI',14,'bold'));self.fmt.set('MP4');self.fmt.pack(side='left')
        self.quality=ctk.CTkOptionMenu(options,values=['360p','480p','720p','1080p','1440p','2160p'],width=120,height=40,corner_radius=12,fg_color=PANEL,button_color='#243650',button_hover_color='#365c91',dropdown_fg_color=PANEL);self.quality.set('1080p');self.quality.pack(side='left',padx=12)
        self.start=ctk.CTkButton(options,text='Descargar ↓',height=46,width=165,corner_radius=15,fg_color=BLUE,hover_color='#b0ceff',text_color=BG,font=('Segoe UI',14,'bold'),command=self.download);self.start.pack(side='right')
        self.stop=ctk.CTkButton(options,text='Cancelar',width=85,height=40,fg_color='transparent',hover_color=PANEL,command=self.cancel,state='disabled');self.stop.pack(side='right',padx=8)
        progress=ctk.CTkFrame(self,fg_color='transparent');progress.grid(row=3,column=0,sticky='ew',padx=32,pady=(0,14))
        self.status=ctk.CTkLabel(progress,text='Un enlace por línea · Hasta 50',text_color=MUTED,anchor='w');self.status.pack(fill='x')
        self.total=ctk.CTkProgressBar(progress,height=5,progress_color=BLUE,fg_color=PANEL);self.total.set(0);self.total.pack(fill='x',pady=(8,0))
        self.list=ctk.CTkScrollableFrame(self,fg_color=PANEL,corner_radius=20,border_width=1,border_color='#233149');self.list.grid(row=4,column=0,sticky='nsew',padx=32)
        self.empty=ctk.CTkLabel(self.list,text='↓',text_color='#365c85',font=('Segoe UI',38));self.empty.pack(pady=(28,4))
        ctk.CTkLabel(self.list,text='Todo listo para empezar',text_color=TEXT,font=('Segoe UI',16,'bold')).pack()
        ctk.CTkLabel(self.list,text='Pega enlaces y elige tu formato.',text_color=MUTED,font=('Segoe UI',12)).pack(pady=(3,24))
        foot=ctk.CTkFrame(self,fg_color='transparent');foot.grid(row=5,column=0,sticky='ew',padx=32,pady=18)
        self.pathlabel=ctk.CTkLabel(foot,text=self.pathtext(),text_color=MUTED,anchor='w');self.pathlabel.pack(side='left')
        ctk.CTkButton(foot,text='Abrir carpeta',width=100,fg_color='transparent',hover_color=PANEL,command=self.open_folder).pack(side='right')
        ctk.CTkButton(foot,text='Detalles',width=70,fg_color='transparent',hover_color=PANEL,command=self.details).pack(side='right')
        self.after(100,self.poll);self.protocol('WM_DELETE_WINDOW',self.close)
    def hero_resize(self,event):
        self.hero.coords(self.folder_window,event.width-24,36)
        self.hero.coords(self.motion_window,event.width-24,78)
    def toggle_motion(self):
        self.motion=not self.motion
        self.motionbutton.configure(text='Partículas: sí' if self.motion else 'Partículas: pausa')
        if self.motion:
            self.last_frame=time.monotonic();self.animate_particles()
        elif self.particle_job is not None:
            self.after_cancel(self.particle_job);self.particle_job=None
    def animate_particles(self):
        self.particle_job=None
        if not self.motion:return
        now=time.monotonic();dt=min(now-self.last_frame,.1);self.last_frame=now
        if self.state()!='iconic':
            w=max(self.hero.winfo_width(),1);h=max(self.hero.winfo_height(),1)
            for p in self.particles:
                p[1]=(p[1]-p[3]*dt)%1
                x=(p[0]+math.sin(now*.3+p[4])*.012)*w;y=p[1]*h;r=p[2]
                self.hero.coords(p[5],x-r,y-r,x+r,y+r)
                self.hero.coords(p[6],x-r*2.8,y-r*2.8,x+r*2.8,y+r*2.8)
        self.particle_job=self.after(33,self.animate_particles)
    def destroy(self):
        if getattr(self,'particle_job',None) is not None:
            self.after_cancel(self.particle_job);self.particle_job=None
        super().destroy()
    def pathtext(self):
        s=str(self.folder);return s if len(s)<54 else '…'+s[-51:]
    def count(self,event=None):self.counter.configure(text=f'{len([l for l in self.links.get("1.0","end").splitlines() if l.strip()])} / 50')
    def paste(self):
        try:
            value=self.clipboard_get();existing=self.links.get('1.0','end').strip()
            self.links.insert('end',('\n' if existing else '')+value.strip());self.count()
        except Exception:pass
    def change_format(self,value):
        self.quality.configure(values=['128 kbps','192 kbps','320 kbps'] if value=='MP3' else ['360p','480p','720p','1080p','1440p','2160p']);self.quality.set('192 kbps' if value=='MP3' else '1080p')
    def pick(self):
        p=filedialog.askdirectory(initialdir=self.folder if self.folder.exists() else Path.home())
        if p:self.folder=Path(p);self.pathlabel.configure(text=self.pathtext())
    def open_folder(self):
        try:
            self.folder.mkdir(parents=True,exist_ok=True)
            if os.name=='nt':os.startfile(str(self.folder))
            else:subprocess.Popen(['xdg-open',str(self.folder)])
        except Exception as e:messagebox.showerror('Carpeta',str(e))
    def download(self):
        if self.busy:return
        try:
            urls=batch_urls(self.links.get('1.0','end'));self.folder.mkdir(parents=True,exist_ok=True)
            node,ffmpeg=dependencies()
            version=subprocess.check_output([node,'--version'],text=True,creationflags=FLAGS)
            if int(version.strip().lstrip('v').split('.')[0])<22:raise ValueError('Actualiza Node.js a una versión LTS actual.')
        except Exception as e:messagebox.showerror('VaoLoad',str(e));return
        for w in self.list.winfo_children():w.destroy()
        self.rows={};self.logs=[];self.done=0;self.total.set(0);self.busy=True;self.set_busy(True)
        for i,url in enumerate(urls):
            frame=ctk.CTkFrame(self.list,fg_color='transparent');frame.pack(fill='x',padx=10,pady=9)
            title=ctk.CTkLabel(frame,text=f'{i+1:02}  ·  '+url.rsplit('=',1)[-1],anchor='w',font=('Segoe UI',12,'bold'));title.pack(fill='x')
            label=ctk.CTkLabel(frame,text='En cola',anchor='w',text_color=MUTED,font=('Segoe UI',11));label.pack(fill='x')
            bar=ctk.CTkProgressBar(frame,height=3,progress_color=BLUE,fg_color='#26334a');bar.set(0);bar.pack(fill='x',pady=(4,0))
            self.rows[i]={'title':title,'state':label,'bar':bar,'result':None}
        self.status.configure(text=f'0 / {len(urls)} · 3 simultáneas')
        self.batch=Batch(self.events.put)
        import re
        quality=re.search(r'\d+',self.quality.get()).group()
        threading.Thread(target=self.batch.run,args=(urls,str(self.folder),self.fmt.get(),quality,node,ffmpeg),daemon=True).start()
    def set_busy(self,on):
        for w in (self.start,self.folderbutton,self.fmt,self.quality,self.pastebutton,self.links):w.configure(state='disabled' if on else 'normal')
        self.stop.configure(state='normal' if on else 'disabled')
    def cancel(self):
        if self.busy and self.batch:
            self.stop.configure(state='disabled');self.status.configure(text='Cancelando…')
            def stop():
                try:self.batch.cancel()
                except Exception as e:self.events.put(('log',0,'Cancelación: '+str(e)))
            threading.Thread(target=stop,daemon=True).start()
    def poll(self):
        for _ in range(300):
            try:kind,i,value=self.events.get_nowait()
            except queue.Empty:break
            row=self.rows.get(i)
            if kind=='batch_done':
                self.busy=False;self.set_busy(False)
                ok=sum(r['result']=='Listo' for r in self.rows.values());err=sum(r['result']=='Error' for r in self.rows.values());cancel=sum(r['result']=='Cancelado' for r in self.rows.values())
                self.status.configure(text=f'{ok} listas'+(f' · {err} con error' if err else '')+(f' · {cancel} canceladas' if cancel else ''));self.total.set(1)
            elif kind=='log':
                self.logs.append(f'[{i+1}] {value}');self.logs=self.logs[-1500:]
            elif row:
                if kind=='title':row['title'].configure(text=f'{i+1:02}  ·  '+value[:85])
                elif kind=='state':row['state'].configure(text=value)
                elif kind=='progress':row['bar'].set(value);row['state'].configure(text=f'Descargando · {value:.0%}')
                elif kind=='done':
                    row['result']=value;row['state'].configure(text=value,text_color='#8edcbb' if value=='Listo' else ('#ffacac' if value=='Error' else MUTED))
                    if value=='Listo':row['bar'].set(1)
                    self.done+=1;self.total.set(self.done/len(self.rows));self.status.configure(text=f'{self.done} / {len(self.rows)} procesadas')
        self.after(100,self.poll)
    def details(self):
        window=ctk.CTkToplevel(self);window.title('Detalles');window.geometry('760x420');box=ctk.CTkTextbox(window,font=('Consolas',11));box.pack(fill='both',expand=True,padx=16,pady=16);box.insert('1.0','\n'.join(self.logs) or 'Sin actividad.');box.configure(state='disabled')
    def close(self):
        if self.busy:
            if not messagebox.askyesno('Cerrar','¿Cancelar las descargas y cerrar?'):return
            self.cancel();self.wait_close();return
        self.destroy()
    def wait_close(self):
        if self.busy:self.after(150,self.wait_close)
        else:self.destroy()
if __name__=='__main__':App().mainloop()
