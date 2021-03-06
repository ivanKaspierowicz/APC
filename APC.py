from tkinter import * 
from tkinter import filedialog
from tkinter.ttk import Progressbar , Combobox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import soundfile as sf
from scipy import ndimage
import scipy.signal as sc
import numpy as np
import matplotlib.pyplot as plt
import csv


def func_calculate():
    if len(RIRs)==0 or cmbx_bandfilter.current()==-1 :
        return
    
    global results
    global signals
    global envelopes
    global averages
    global channels
    global fs
    
    changestate(0)
    
    channels = RIRchannels[:]
    strbands = bands_labels[cmbx_bandfilter.current()][cmbx_minband.current():cmbx_minband.current()+cmbx_maxband.current()+1]
    bands = bands_centers[cmbx_bandfilter.current()][cmbx_minband.current():cmbx_minband.current()+cmbx_maxband.current()+1]
    results = np.zeros([len(parameters),len(bands)+1,len(RIRs),2])
    signals = []
    envelopes = []
    fs = samplerate[:]
    
    if cmbx_bandfilter.current()==0:
        freclim = (2**(1/2))
    elif cmbx_bandfilter.current()==1:
        freclim = (2**(1/6))
    
    total_steps = len(bands)*sum(channels)
    bar_step = 0
    pbar.grid()
    btn_calculate.grid_remove()
    
    for s in range(len(RIRs)):
        
        list.append(signals,[])
        list.append(envelopes,[])

        for c in range(channels[s]): 
            
            list.append(signals[s],[])
            list.append(envelopes[s],[])
            
            for b in range(len(bands)+1):
                
                if b==0:
                    finf = (2/fs[s]) * bands[0]/freclim
                    fsup = (2/fs[s]) * bands[-1]*freclim
                    winlen = int(1000*np.log10(fs[s]/ (bands[0]/freclim)))
                else:
                    finf = (2/fs[s]) * bands[b-1]/freclim
                    fsup = (2/fs[s]) * bands[b-1]*freclim
                    winlen = int(1000*np.log10(fs[s]/ (bands[b-1]/freclim)))                
                if fsup>1:
                        fsup = (fs[s]-1)/fs[s]
                sos = sc.butter(8,[finf,fsup],btype="band",output="sos")
                if reversedcheck.get()==1:
                    sgn = sc.sosfiltfilt(sos,np.flip(RIRs[s][:,c]))
                    list.append(signals[s][c],np.flip(sgn))
                else:
                    sgn = sc.sosfiltfilt(sos,RIRs[s][:,c])
                    list.append(signals[s][c],sgn)
                
                signals[s][c][b] = np.abs(signals[s][c][b])
                IRstart = np.where(signals[s][c][b][0:np.argmax(signals[s][c][b])]<=np.max(signals[s][c][b])/10)[0]
                if len(IRstart)==0:
                    IRstart=0
                else:
                    IRstart=IRstart[-1]
                signals[s][c][b] = signals[s][c][b][IRstart:]
                signals[s][c][b][signals[s][c][b]==0]=0.00000001
                signals[s][c][b] = 20*np.log10(signals[s][c][b])
                
                if cmbx_chunk.current()==0:
                    print(lundeby)
                elif cmbx_chunk.current()==1:
                    print(pepino)
                elif cmbx_chunk.current()==2:
                    [IRend,env] = metodo_propio(signals[s][c][b],fs[s],winlen)
                
                if cmbx_envelope.current()==0:
                    h2 = 10**(signals[s][c][b][0:IRend]/10)
                    env =10*np.log10( np.flip(np.cumsum(np.flip(h2)))/np.sum(h2) )
                elif cmbx_envelope.current()==1:
                    if IRend+1+winlen<len(signals[s][c][b]):
                        env = ndimage.median_filter(signals[s][c][b][0:IRend+1+winlen],winlen)
                    else:
                        env = ndimage.median_filter(signals[s][c][b],winlen)
                    env = env[int(winlen/2):int(len(env)-winlen/2)]
                elif cmbx_envelope.current()==2:
                    if cmbx_chunk.current()==2:
                        env = env[0:IRend+1]
                    else:
                        if IRend+1+winlen<len(signals[s][c][b]):
                            env = mediamovil(signals[s][c][b][0:IRend+winlen],winlen)
                        else:
                            env = mediamovil(signals[s][c][b],winlen)          
                list.append(envelopes[s][c],env)
                
                
                edtsamples = getsamplesbetween(envelopes[s][c][b],0,-10)
                results[0,b,s,c] = -60/(slope(edtsamples)*fs[s])
                
                t20samples = getsamplesbetween(envelopes[s][c][b],-5,-25)
                results[1,b,s,c] = -60/(slope(t20samples)*fs[s])
                
                t30samples = getsamplesbetween(envelopes[s][c][b],-5,-35)
                results[2,b,s,c] = -60/(slope(t30samples)*fs[s])
                
                c50i = np.int(0.05*fs[s]+1)
                num = np.sum(10**(signals[s][c][b][0:c50i]/10))
                den = np.sum(10**(signals[s][c][b][c50i:]/10))        
                results[3,b,s,c] = 10*np.log10(num/den)
                 
                c80i = np.int(0.08*fs[s]+1)
                num = np.sum(10**(signals[s][c][b][0:c80i]/10))
                den = np.sum(10**(signals[s][c][b][c80i:]/10))        
                results[4,b,s,c] = 10*np.log10(num/den)
                
                if channels[s]==2:
                    results[7,b,s,c] = 1997             
                    
                bar_step += 100/total_steps 
                progress.set(bar_step)
                APC.update()
                    
    averages = np.zeros([len(rowsaverage),len(bands)+1,len(parameters)-1])
    averages[0,:,:] = np.transpose(np.sum(results[0:-1,:,:,:],axis=(2,3))/sum(channels))
    averages[1,:,:] = np.transpose(np.max(results[0:-1,:,:,:],axis=(2,3)))
    minresul = results[:,:,:,0]+0
    minindex = (results[:,:,:,0]>results[:,:,:,1])*(results[:,:,:,1]!=0)
    minresul[minindex] = results[minindex,1]
    averages[2,:,:] = np.transpose(np.min(minresul[0:-1,:],axis=2))
    averages[3,:,:] = np.transpose(np.var(results[0:-1,:,:,0],axis=2))


    for i in range(len(rowsaverage)+1):
        for j in range(len(bands_labels[-1])+1):
            if j<=len(bands):
                if i==0 and j!=0:
                    table1[i][j+1]["text"] = strbands[j-1]
                    table1[i][j+1].grid()
                elif i!=0:
                    table1[i][j+1]["text"] = str(np.round(averages[i-1,j,0],2)) 
                    table1[i][j+1].grid()
            else:
                table1[i][j+1].grid_remove()
    
    for i in range(len(parameters)+1):
        for j in range(len(bands_labels[-1])+1):
            if j<=len(bands):
                if i==0 and j!=0:
                    table2[i][j+1]["text"] = strbands[j-1]
                    table2[i][j+1].grid()
                elif i!=0:
                    table2[i][j+1]["text"] = str(np.round(results[i-1,j,0,0],2)) 
                    table2[i][j+1].grid()
            else:
                table2[i][j+1].grid_remove()
    
    
    cmbx_bandplt["values"] = ("global",)+strbands
    cmbx_IRplt["values"] = lstbx_IRs.get(0,"end")+()
    cmbx_bandplt.current(0)
    cmbx_IRplt.current(0)
    cmbx_channels["values"] = tuple(range(1,channels[0]+1))
    cmbx_channels.current(0)
    table1[0][0].current(0) 
    refresh_graphtable1("")
    refresh_graph2()
    progress.set(0)
    btn_calculate.grid()
    pbar.grid_remove()
    changestate(1)
    return

def func_exptable():
    if len(cmbx_IRplt["values"])!=0:
        filename = filedialog.asksaveasfilename(title="Save current table", filetypes=[("CSV File", "*.csv")])
        if not filename: return
        with open(filename, mode='w') as file:
            writer = csv.writer(file, delimiter=',')
            bandsrow = [''] + [cmbx_bandplt["values"][:]]
            writer.writerow(bandsrow)
            if btn_show["text"]=="Show average":
                res = results[:,:,cmbx_IRplt.current(),cmbx_channels.current()]
                for k in range(len(parameters)):
                    row = [parameters[k]] + list(res[k])
                    writer.writerow(row)
                row = ["RIR:"] + [cmbx_IRplt.get()] + ["Channel:"] + [cmbx_channels.get()]
                writer.writerow(row) 
            else:
                ave = averages[:,:,table1[0][0].current()]
                for k in range(len(rowsaverage)):
                    row = [rowsaverage[k]] + list(ave[k])
                    writer.writerow(row)
                row = ["Parameter:"] + [table1[0][0].get()] + ["RIRs:"] + [cmbx_IRplt["values"]]
                writer.writerow(row)  
    return

def changestate(onoff):
    if onoff==1:
        btn_clearall["state"] = NORMAL
        btn_clearselected["state"] = NORMAL
        btn_load["state"] = NORMAL
        btn_sweep["state"] = NORMAL
        cmbx_bandfilter["state"] = NORMAL
        cmbx_chunk["state"] = NORMAL
        cmbx_envelope["state"] = NORMAL
        cmbx_maxband["state"] = NORMAL
        cmbx_minband["state"] = NORMAL
        chkbtn_reverse["state"] = NORMAL
    else:
        btn_clearall["state"] = DISABLED
        btn_clearselected["state"] = DISABLED
        btn_load["state"] = DISABLED
        btn_sweep["state"] = DISABLED
        cmbx_bandfilter["state"] = DISABLED
        cmbx_chunk["state"] = DISABLED
        cmbx_envelope["state"] = DISABLED
        cmbx_maxband["state"] = DISABLED
        cmbx_minband["state"] = DISABLED
        chkbtn_reverse["state"] = DISABLED
    return

def slope(data):
    n = len(data)/1
    x = np.arange(0,n)/1
    m = ( n*np.sum(x*data)-np.sum(x)*np.sum(data) ) / ( n*np.sum(x**2)-np.sum(x)**2 )
    return m

def getsamplesbetween(data,Ls,Li):
    supe = np.where(data>=np.max(data)+Ls)[0][-1]
    infe = np.where(data<np.max(data)+Li)[0]
    infe = infe[infe>supe][0]
    samples = data[supe+1:infe]
    return samples

def mediamovil(data,k):
    w = np.concatenate([np.zeros([len(data)-1]),np.ones([k])/k])
    dataz = np.concatenate([data,np.zeros([k-1])])
    fftdataz = np.fft.rfft(dataz)
    fftw = np.fft.rfft(w)
    mmf = np.fft.irfft(fftdataz*fftw)
    mmf = mmf[0:len(data)-k+1]
    return mmf

def metodo_propio(data,fs,k):
    mmf = mediamovil(data, k)
    mmf = np.concatenate([mmf,np.ones([fs])*mmf[-1]])
    indexmax = np.argmax(mmf)
    levelmax = np.max(mmf)
    M = (mmf[-1]-levelmax)/(len(mmf)-indexmax)
    B = (levelmax-M*indexmax)
    cut = np.argmax(M*range(len(mmf))[indexmax:]+B-mmf[indexmax:])+indexmax
    cut = np.int(cut)
    mmf = np.concatenate([mmf[0:cut],np.ones([fs])*mmf[cut]])
    M = (mmf[-1]-levelmax)/(len(mmf)-indexmax)
    B = (levelmax-M*indexmax)
    cut = np.argmax(M*range(len(mmf))[indexmax:]+B-mmf[indexmax:])+indexmax
    cut = np.int(cut)
    return cut , mmf

def func_load():
    name = filedialog.askopenfilenames(title="Load RIRs files",filetypes=[("WAV Audio","*.wav")])
    for k in range(len(name)):
        [sgn,frec] = sf.read(name[k])
        if len(np.shape(sgn))==2:
            list.append(RIRchannels,np.shape(sgn)[1])
        elif len(np.shape(sgn))==1:
            list.append(RIRchannels,1)
            sgn.resize([len(sgn),1])
        else:
            return
        lstbx_IRs.insert("end",name[k])
        list.append(RIRs,sgn)
        list.append(samplerate,frec)
    return

def func_sweep():
    SSname = filedialog.askopenfilenames(title="Load Sweep files",filetypes=[("WAV Audio","*.wav")])
    IFname = filedialog.askopenfilename(title="Load Inverse filter file",filetypes=[("WAV Audio","*.wav")])
    if len(IFname)!=0 and len(SSname)!=0:
        [ifilt,fs_ifilt] = sf.read(IFname)
        for k in range(len(SSname)):
            [ss,fs_ss] = sf.read(SSname[k])
            if fs_ss!=fs_ifilt:
                return
            sgn = sc.fftconvolve(ifilt,ss,mode="valid")
            sgn = sgn/np.max(np.abs(sgn))
            if len(np.shape(sgn))==2:
                list.append(RIRchannels,np.shape(sgn)[1])
            elif len(np.shape(sgn))==1:
                list.append(RIRchannels,1)
                sgn.resize([len(sgn),1])
            else:
                return
            lstbx_IRs.insert("end",SSname[k])
            list.append(RIRs,sgn)
            list.append(samplerate,fs_ss)
    return

def func_clearall():
    list.clear(RIRs)
    list.clear(samplerate)
    list.clear(RIRchannels)
    lstbx_IRs.delete(0,"end")
    return

def func_clearselected():
    for k in lstbx_IRs.curselection():
        list.pop(RIRs,lstbx_IRs.curselection()[0])
        list.pop(samplerate,lstbx_IRs.curselection()[0])
        list.pop(RIRchannels,lstbx_IRs.curselection()[0])
        lstbx_IRs.delete(lstbx_IRs.curselection()[0])
    return

def func_expplot():
    if len(cmbx_IRplt["values"])!=0:
        filename = filedialog.asksaveasfile(title="Save current plot",filetypes=[("PNG Image","*.png")])
        if not filename: return
        if btn_show["text"]=="Show average":
            figgraph2.savefig(filename.name,facecolor="w")
        else:
            figgraph1.savefig(filename.name,facecolor="w")
    return

def func_show():
    if btn_show["text"]=="Show average":
        btn_show["text"] = "Show RIRs"
        frame_pltsettings.grid_remove()
        get_widz2.grid_remove()
        frame_table2.grid_remove()
        get_widz1.grid()
        frame_table1.grid()
    else:
        btn_show["text"] = "Show average"
        frame_pltsettings.grid()
        get_widz2.grid()
        frame_table2.grid()
        get_widz1.grid_remove()
        frame_table1.grid_remove()
    return

def func_bandfilter(event):
    if cmbx_bandfilter.current()==0:
        cmbx_minband["values"] = bands_labels[0]
        cmbx_maxband["values"] = bands_labels[0]
        cmbx_minband.current(0)
        cmbx_maxband.current(len(bands_labels[0])-1)
    elif cmbx_bandfilter.current()==1:
        cmbx_minband["values"] = bands_labels[1]
        cmbx_maxband["values"] = bands_labels[1]
        cmbx_minband.current(0)
        cmbx_maxband.current(len(bands_labels[1])-1)
    return

def func_limitband(event):
    if cmbx_bandfilter.current()==0:
        cmbx_maxband["values"] = bands_labels[0][cmbx_minband.current():]
        cmbx_minband["values"] = bands_labels[0][0:cmbx_maxband.current()+cmbx_minband.current()+1]
    elif cmbx_bandfilter.current()==1:
        cmbx_maxband["values"] = bands_labels[1][cmbx_minband.current():]
        cmbx_minband["values"] = bands_labels[1][0:cmbx_maxband.current()+cmbx_minband.current()+1]
    return

def refresh_graphtable1(event):
    if len(cmbx_IRplt["values"])!=0:
        aver =  averages[0,:,table1[0][0].current()]
        maxi = averages[1,:,table1[0][0].current()]
        mini = averages[2,:,table1[0][0].current()]
        f = range(len(cmbx_bandplt["values"]))
        graph1.cla()
        graph1.plot(aver[0],"ok")
        graph1.errorbar(0,aver[0],yerr=np.abs(np.array([[mini[0]],[maxi[0]]])-aver[0]),fmt='--o')
        graph1.fill_between(f[1:],mini[1:],maxi[1:],facecolor='b',alpha=0.3)
        graph1.plot(f[1:],aver[1:],"r")
        graph1.set_xlabel("Frecuency [Hz]")
        graph1.set_xticks(f)
        graph1.set_xticklabels(cmbx_bandplt["values"])
        graph1.grid()
        if table1[0][0].current()==0:
            graph1.set_ylabel("EDT [s]")
            graph1.set_ylim(ymin=0)
        elif table1[0][0].current()==1:
            graph1.set_ylabel("T20 [s]")
            graph1.set_ylim(ymin=0)
        elif table1[0][0].current()==2:
            graph1.set_ylabel("T30 [s]")
            graph1.set_ylim(ymin=0)
        elif table1[0][0].current()==3:
            graph1.set_ylabel("C50 [dB]")
        elif table1[0][0].current()==4:
            graph1.set_ylabel("C80 [dB]")
        elif table1[0][0].current()==5:
            graph1.set_ylabel("Tt [s]")
            graph1.set_ylim(ymin=0)
        elif table1[0][0].current()==6:          
            graph1.set_ylabel("EDTt [s]")
            graph1.set_ylim(ymin=0)
        canv1.draw()
        for i in range(len(rowsaverage)):
            for j in range(len(cmbx_bandplt["values"])):
                table1[i+1][j+1]["text"] = str(np.round(averages[i,j,table1[0][0].current()],2)) 
    
    return

def func_channels(event):
    if len(cmbx_IRplt["values"])!=0:
        refresh_table2()
        refresh_graph2()
    return

def func_bandplot(event):
    if len(cmbx_IRplt["values"])!=0:
        refresh_graph2()
    return

def func_IRplot(event):
    if len(cmbx_IRplt["values"])!=0:
        cmbx_channels["values"] = tuple(range(1,channels[cmbx_IRplt.current()]+1))
        cmbx_channels.current(0)
        refresh_table2()
        refresh_graph2()
    return

def refresh_table2():
    for i in range(len(parameters)):
        for j in range(len(cmbx_bandplt["values"])):
            table2[i+1][j+1]["text"] = str(np.round(results[i,j,cmbx_IRplt.current(),cmbx_channels.current()],2)) 
    return

def refresh_graph2():
    sgn = signals[cmbx_IRplt.current()][cmbx_channels.current()][cmbx_bandplt.current()]
    env = envelopes[cmbx_IRplt.current()][cmbx_channels.current()][cmbx_bandplt.current()]
    frecs = fs[cmbx_IRplt.current()]
    graph2.cla()
    if len(sgn)<2*len(env):
        end=len(sgn)
    else:
        end=len(env)*2
    graph2.plot(np.arange(0,end)/frecs,sgn[0:end])
    graph2.plot(np.arange(0,len(env))/frecs,env)
    graph2.set_xlim(xmax=end/frecs)
    graph2.set_xlabel("Time [s]")
    graph2.set_ylabel("Level [dBFS]")
    graph2.grid()
    canv2.draw()
    return

RIRs = []
samplerate = []
RIRchannels = []
bands_centers = [(31.5,63,125,250,500,1000,2000,4000,8000,16000),(25,31.5,40,50,63,80,100,125,160,200,250,315,400,500,630,800,1000,1250,1600,2000,2500,3150,4000,5000,6300,8000,10000,12500,16000,20000)]
bands_labels = [("31.5","63","125","250","500","1k","2k","4k","8k","16k"),("25","31.5","40","50","63","80","100","125","160","200","250","315","400","500","630","800","1k","1.25k","1.6k","2k","2.5k","3.15k","4k","5k","6.3k","8k","10k","12.5k","16k","20k")]
parameters = ("EDT", "T20", "T30", "C50", "C80","Tt", "EDTt", "IACC")
rowsaverage = ("Average","Max","Min","Sigma")

APC = Tk()
APC.title("Acoustic Parameters Calculator")
APC.rowconfigure(0,weight=1)
APC.columnconfigure(1,weight=1)
APC["padx"] = "2"
APC["pady"] = "2"
APC.geometry("1000x600")

figgraph1 = Figure(constrained_layout=True)
graph1 = figgraph1.add_subplot(111)
graph1.set_xlabel("Frecuency [Hz]")
graph1.set_ylabel("")
r , g , b = APC.winfo_rgb(APC["bg"])
figgraph1.set_facecolor([r/65536,g/65536,b/65536])

canv1 = FigureCanvasTkAgg(figgraph1, master = APC)
canv1.draw()
get_widz1 = canv1.get_tk_widget()
get_widz1.grid(row=0, column=1, padx=4, pady=4, sticky="ewns")
get_widz1.grid_remove()

figgraph2 = Figure(constrained_layout=True)
graph2 = figgraph2.add_subplot(111)
graph2.set_xlabel("Time [s]")
graph2.set_ylabel("Level [dBFS]")
graph2.set_ylim([-100,0])
r , g , b = APC.winfo_rgb(APC["bg"])
figgraph2.set_facecolor([r/65536,g/65536,b/65536])

canv2 = FigureCanvasTkAgg(figgraph2, master = APC)
canv2.draw()
get_widz2 = canv2.get_tk_widget()
get_widz2.grid(row=0, column=1, padx=4, pady=4, sticky="ewns")


frame_menu = Frame(APC)
frame_menu.grid(row=0, column=0, sticky="ewns", padx=2, pady=2)
frame_menu.rowconfigure(3,weight=1)

progress = DoubleVar()
pbar = Progressbar(frame_menu, variable=progress)
pbar.grid(row=4, column=0, columnspan=2, sticky="ewns", padx=2, pady=2)

btn_load = Button(frame_menu, text="Load RIRs", command=func_load)
btn_load.grid(row=0, column=0, padx=2, pady=2, sticky="ewns")

btn_sweep = Button(frame_menu, text="Load Sweep", command=func_sweep)
btn_sweep.grid(row=0, column=1, padx=2, pady=2, sticky="ewns")

btn_clearall = Button(frame_menu, text="Clear all", command=func_clearall)
btn_clearall.grid(row=1, column=0, padx=2, pady=2, sticky="ewns")

btn_clearselected = Button(frame_menu, text="Clear selected", command=func_clearselected)
btn_clearselected.grid(row=1, column=1, padx=2, pady=2, sticky="ewns")

btn_calculate = Button(frame_menu, text="Calculate", font=("Arial",12,"bold"),command=func_calculate)
btn_calculate.grid(row=4, column=0,columnspan=2, sticky="ewns", padx=2, pady=2)

btn_show = Button(frame_menu, text="Show average", command=func_show)
btn_show.grid(row=5, column=0, columnspan=2, sticky="ewns", padx=2, pady=2)

btn_expplot = Button(frame_menu, text="Export plot", command=func_expplot)
btn_expplot.grid(row=6, column=0, sticky="ewns", padx=2, pady=2)

btn_exptable = Button(frame_menu, text="Export table", command=func_exptable)
btn_exptable.grid(row=6, column=1, sticky="ewns", padx=2, pady=2)

frame_IRs = Frame(frame_menu)
frame_IRs.grid(row=3, column=0, columnspan=2, sticky="ewns", padx=2, pady=2)
frame_IRs.columnconfigure(0, weight=1)
frame_IRs.rowconfigure(0, weight=1)
scrollbarV=Scrollbar(frame_IRs,orient="vertical")
scrollbarV.grid(row=0,column=1,sticky="ewns")
scrollbarH=Scrollbar(frame_IRs,orient="horizontal")
scrollbarH.grid(row=1,column=0,sticky="ewns")
lstbx_IRs = Listbox(frame_IRs, selectmode="extended")
lstbx_IRs.grid(row=0, column=0, sticky="ewns")
lstbx_IRs.config(yscrollcommand=scrollbarV.set,xscrollcommand=scrollbarH.set)
scrollbarV.config(command=lstbx_IRs.yview)
scrollbarH.config(command=lstbx_IRs.xview)

frame_settings = Frame(frame_menu)
frame_settings.grid(row=2, column=0, columnspan=2, sticky="ewns", padx=2, pady=2)

lbl_settings = Label(frame_settings, text="Settings", anchor="center")
lbl_settings.grid(row=0, column=0,columnspan=4, sticky="ewns")

lbl_bandfilter = Label(frame_settings, text="Band filter:", anchor="e")
lbl_bandfilter.grid(row=1, column=0, sticky="ewns")

cmbx_bandfilter = Combobox(frame_settings, values=("Octave","Third"), state="readonly", width=7)
cmbx_bandfilter.grid(row=1, column=1, sticky="ewns", pady=1)
cmbx_bandfilter.bind("<<ComboboxSelected>>",func_bandfilter)

lbl_minband = Label(frame_settings, text="Min band:", anchor="e")
lbl_minband.grid(row=2, column=0, sticky="ewns")

cmbx_minband = Combobox(frame_settings, state="readonly", width=7)
cmbx_minband.grid(row=2, column=1, sticky="ewns", pady=1)
cmbx_minband.bind("<<ComboboxSelected>>",func_limitband)

lbl_maxband = Label(frame_settings, text="Max band:", anchor="e")
lbl_maxband.grid(row=3, column=0, sticky="ewns")

cmbx_maxband = Combobox(frame_settings, state="readonly", width=7)
cmbx_maxband.grid(row=3, column=1, sticky="ewns", pady=1)
cmbx_maxband.bind("<<ComboboxSelected>>",func_limitband)

lbl_envelope = Label(frame_settings, text="Envelope:", anchor="e")
lbl_envelope.grid(row=1, column=2, sticky="ewns")

cmbx_envelope = Combobox(frame_settings, values=("Schoreder","Median MF","Mean MF"), state="readonly", width=10)
cmbx_envelope.current(0)
cmbx_envelope.grid(row=1, column=3, sticky="ewns", pady=1)

lbl_chunk = Label(frame_settings, text="IR chunk:", anchor="e")
lbl_chunk.grid(row=2, column=2, sticky="ewns")

cmbx_chunk = Combobox(frame_settings, values=("Lundeby", "Pepino", "Roge"), state="readonly", width=10)
cmbx_chunk.current(0)
cmbx_chunk.grid(row=2, column=3, sticky="ewns", pady=1)

reversedcheck = IntVar()
chkbtn_reverse = Checkbutton(frame_settings, text="Reversed Filtering", variable=reversedcheck)
chkbtn_reverse.grid(row=3, column=2, columnspan=2, sticky="ewns")

frame_pltsettings = Frame(frame_menu)
frame_pltsettings.grid(row=7, column=0, columnspan=2)

lbl_IRplt = Label(frame_pltsettings,text="RIR plot:")
lbl_IRplt.grid(row=0, column=0, sticky="ens",pady=2)

cmbx_IRplt = Combobox(frame_pltsettings,state="readonly")
cmbx_IRplt.grid(row=0, column=1, columnspan=3, sticky="wns", pady=2, padx=2)
cmbx_IRplt.bind("<<ComboboxSelected>>",func_IRplot)

lbl_bandplt = Label(frame_pltsettings,text="Band:")
lbl_bandplt.grid(row=1, column=0, sticky="ens", pady=2)

cmbx_bandplt = Combobox(frame_pltsettings,state="readonly",width=6)
cmbx_bandplt.grid(row=1, column=1, sticky="wns", pady=2, padx=2)
cmbx_bandplt.bind("<<ComboboxSelected>>",func_bandplot)

lbl_channels = Label(frame_pltsettings,text="Channel:")
lbl_channels.grid(row=1, column=2, sticky="ens", pady=2)

cmbx_channels = Combobox(frame_pltsettings,state="readonly",width=6)
cmbx_channels.grid(row=1, column=3, sticky="wns", pady=2, padx=2)
cmbx_channels.bind("<<ComboboxSelected>>",func_channels)

frame_table1 = Frame(APC)
frame_table1.grid(row=1,column=0,columnspan=2,padx=4,pady=4,sticky="ewns")
frame_table1.grid_remove()
for i in range(len(rowsaverage)+1):
    for j in range(len(bands_labels[-1])+2):
        if i==0 and j>1:
            table1[i] = table1[i] + [Label(frame_table1, text=bands_labels[1][j-2], bg="white", relief="solid",borderwidth=1)]
            table1[i][j].grid(row=i,column=j,sticky="ewns")
            frame_table1.columnconfigure(j, weight=1)
        elif i==0 and j==1:
            table1[i] = table1[i] + [Label(frame_table1, text="global", bg="white", relief="solid",borderwidth=1)]
            table1[i][j].grid(row=i,column=j,sticky="ewns")
            frame_table1.columnconfigure(j, weight=1)
        
        elif i!=0 and j==0:
            table1 = table1 + [[Label(frame_table1,text=rowsaverage[i-1], bg="white", relief="solid",borderwidth=1)]]
            table1[i][j].grid(row=i,column=j,sticky="ewns")
        elif i!=0 and j!=0:
            table1[i] = table1[i] + [Label(frame_table1,text="", bg="white", relief="solid",borderwidth=1)]
            table1[i][j].grid(row=i,column=j,sticky="ewns")
        elif i==0 and j==0:
            table1=[[Combobox(frame_table1, values=parameters[0:-1], width=5, state="readonly")]]
            table1[i][j].current(0)
            table1[i][j].bind("<<ComboboxSelected>>",refresh_graphtable1)
            table1[i][j].grid(row=i, column=j, sticky="ewns")

frame_table2 = Frame(APC)
frame_table2.grid(row=1,column=0,columnspan=2,padx=4,pady=4,sticky="ewns")
for i in range(len(parameters)+1):
    for j in range(len(bands_labels[-1])+2):
        if i==0 and j>1:
            table2[i] = table2[i] + [Label(frame_table2, text=bands_labels[1][j-2], bg="white", relief="solid",borderwidth=1)]
            table2[i][j].grid(row=i,column=j,sticky="ewns")
            frame_table2.columnconfigure(j, weight=1)
        elif i==0 and j==1:
            table2[i] = table2[i] + [Label(frame_table2, text="global", bg="white", relief="solid",borderwidth=1)]
            table2[i][j].grid(row=i,column=j,sticky="ewns")
            frame_table2.columnconfigure(j, weight=1)
        elif i!=0 and j==0:
            table2 = table2 + [[Label(frame_table2,text=parameters[i-1], bg="white", relief="solid",borderwidth=1)]]
            table2[i][j].grid(row=i,column=j,sticky="ewns")
        elif i!=0 and j!=0:
            table2[i] = table2[i] + [Label(frame_table2,text="", bg="white", relief="solid",borderwidth=1)]
            table2[i][j].grid(row=i,column=j,sticky="ewns")
        elif i==0 and j==0:
            table2=[[""]]

APC.mainloop()