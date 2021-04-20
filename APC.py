from tkinter import * 
from tkinter import filedialog
from tkinter.ttk import Progressbar , Combobox , Treeview
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import soundfile as sf


def func_calculate():
    if len(RIRs)==0:
        return
    if str.isdigit(ent_winlen.get())==0 and cmbx_envelope.current()!=0:
        return
    
    resultados = np.zeros([len(parameters),len(bands[cmbx_bandfilter.current()])+1,len(RIRs)])
    signals = [[]]
    envelopes = [[]]
    for s in range(len(RIRs)):
        for b in range(len(bands[cmbx_bandfilter.current()])+1):
            if b==0:
                winlen = 10*np.int(fs[s]/bands[0])
                signals[s][b] = RIRs[s]
            else:
                winlen = 10*np.int(fs[s]/bands[b-1])
                if reversedcheck.get()==1:
                    print(6)#flip filtrar flip
                else:
                    print(8)#filtrar
            
            signals[s][b] = 20*np.log10(np.abs(signals[s][b]))
            IRstart = np.where(signals[s][b][0:np.argmax(signals[s][b])]<=np.max(signals[s][b])/10)[0][-1]
            signals[s][b] = signals[s][b][IRstart:]
            
            if cmbx_IRplt.current()==0:
                print(lundeby)
            elif cmbx_IRplt.current()==1:
                print(pepino)
            elif cmbx_IRplt.current()==2:
                [IRend,meanmf] = metodo_propio(signals[s][b],fs[s],winlen)
            
            if cmbx_envelope.current()==0:
                print(schoreder)
            elif cmbx_envelope.current()==1:
                if IRend+1+winlen<len(signals[s][b]):
                    env = ndimage.median_filter(signals[s][b][0:IRend+1+winlen],winlen)
                else:
                    env = ndimage.median_filter(signals[s][b],winlen)
                env = env[int(winlen/2):int(len(env)-winlen/2)]
            elif cmbx_envelope.current()==2:
                if cmbx_IRplt.current()==2:
                    env = env[0:IRend+1]
                else:
                    if IRend+1+winlen<len(signals[s][b]):
                        env = mediamovil(signals[s][b][0:IRend+winlen],winlen)
                    else:
                        env = mediamovil(signals[s][b],winlen)
            envelopes[s] = list.append(envelopes[s],env)
            
            edtsamples = getsamplesbetween(envelopes[s][b],0,-10)
            resultados[0,b,s] = 60/(slope(edtsamples)*fs[s])
            
            t20samples = getsamplesbetween(envelopes[s][b],-5,-25)
            resultados[1,b,s] = 60/(slope(t20samples)*fs[s])
            
            t30samples = getsamplesbetween(envelopes[s][b],-5,-35)
            resultados[2,b,s] = 60/(slope(t30samples)*fs[s])
            
            c50 =
            
            c80 = 
    return

def slope(data):
    n = len(data)
    x = np.arange(0,n)
    m = ( n*np.sum(x*data)+np.sum(x)*np.sum(data) ) / ( n*np.sum(x**2)-np.sum(x)**2 )
    return m

def getsamplesbetween(data,Ls,Li):
    sup = np.where(data>=np.max(data)+Ls)[0][-1]
    inf = np.where(data<np.max(data)+Li)[0][0]
    samples = data[sup+1:inf]
    return samples

def mediamovil(data,k):
    w = np.concatenate([np.zeros([len(data)-1]),np.ones([k])/k])
    data = np.concatenate([data,np.zeros([k-1])])
    fftdata = np.fft.rfft(data)
    fftw = np.fft.rfft(w)
    mmf = np.fft.irfft(fftdata*fftw)
    mmf = mmf[0:len(data)-k+1]
    return mmf

def metodo_propio(data,fs,k):
    
    #media movil
    mmf=mediamovil(data,k)
    #recta
    mmf = np.concatenate([mmf,np.ones([fs])*mmf[-1]])
    indexmax = np.argmax(mmf)
    levelmax = np.max(mmf)
    M = (mmf[-1]-levelmax)/(len(mmf)-indexmax)
    B = (levelmax-M*indexmax)
    cut = np.argmax(M*range(len(mmf))[indexmax:]+B-mmf[indexmax:])+k/2+indexmax
    
    return cut , mmf

def func_load():
    name = filedialog.askopenfilenames(title="Load RIRs files",filetypes=[("WAV Audio",".wav")])
    for k in range(len(name)):
        lstbx_IRs.insert("end",name[k])
        [sgn,frec]=sf.read(name[k])
        list.append(RIRs,sgn)
        list.append(fs,frec)
    return

def func_clearall():
    list.clear(RIRs)
    list.clear(fs)
    lstbx_IRs.delete(0,"end")
    return

def func_clearselected():
    for k in lstbx_IRs.curselection():
        list.pop(RIRs,lstbx_IRs.curselection()[0])
        list.pop(fs,lstbx_IRs.curselection()[0])
        lstbx_IRs.delete(lstbx_IRs.curselection()[0])
    return

def func_show():
    if btn_show["text"]=="Show average":
        btn_show["text"]="Show RIRs"
        lbl_bandplt.grid_remove()
        lbl_IRplt.grid_remove()
        cmbx_IRplt.grid_remove()
        cmbx_bandplt.grid_remove()
        get_widz2.grid_remove()
        frame_table2.grid_remove()
        get_widz1.grid()
        frame_table1.grid()
    else:
        btn_show["text"]="Show average"
        lbl_bandplt.grid()
        lbl_IRplt.grid()
        cmbx_IRplt.grid()
        cmbx_bandplt.grid()
        get_widz2.grid()
        frame_table2.grid()
        get_widz1.grid_remove()
        frame_table1.grid_remove()
    return

def hidesettings(event):
    if cmbx_envelope.current()==0:
        ent_winlen.grid_remove()
        lbl_winlen.grid_remove()
        lbl_chunk.grid()
        cmbx_chunk.grid()
    else:
        ent_winlen.grid()
        lbl_winlen.grid()
        lbl_chunk.grid_remove()   
        cmbx_chunk.grid_remove()
    return

RIRs=[]
fs=[]
bands=[(63,125,250,500,1000,2000,4000,8000),("50","63","80","100","125","160","200","250","315","400","500","630","800","1k","1.25k","1.6k","2k","2.5k","3.15k","4k","5k","6.3k","8k","10k")]
bands_labels=[("63","125","250","500","1k","2k","4k","8k"),("50","63","80","100","125","160","200","250","315","400","500","630","800","1k","1.25k","1.6k","2k","2.5k","3.15k","4k","5k","6.3k","8k","10k")]
parameters=("EDT", "T20", "T30", "C50", "C80", "Tt", "EDTt")
filas1=("Average","Max","Min","Sigma")

APC = Tk()
APC.title("Acoustic Parameters Calculator")
APC.rowconfigure(0,weight=1)
APC.columnconfigure(1,weight=1)
APC["padx"]="2"
APC["pady"]="2"
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
r , g , b = APC.winfo_rgb(APC["bg"])
figgraph2.set_facecolor([r/65536,g/65536,b/65536])

canv2 = FigureCanvasTkAgg(figgraph2, master = APC)
canv2.draw()
get_widz2 = canv2.get_tk_widget()
get_widz2.grid(row=0, column=1, padx=4, pady=4, sticky="ewns")


frame_menu = Frame(APC)
frame_menu.grid(row=0, column=0, sticky="ewns", padx=2, pady=2)
frame_menu.rowconfigure(3,weight=1)
btn_load = Button(frame_menu, text="Load IRs", command=func_load)
btn_load.grid(row=0, column=0, padx=2, pady=2, sticky="ewns")

btn_clear = Button(frame_menu, text="Clear all", command=func_clearall)
btn_clear.grid(row=1, column=0, padx=2, pady=2, sticky="ewns")

btn_clear = Button(frame_menu, text="Clear selected", command=func_clearselected)
btn_clear.grid(row=2, column=0, padx=2, pady=2, sticky="ewns")

btn_calculate = Button(frame_menu, text="Calculate", font=("Arial",12,"bold"),command=func_calculate)
btn_calculate.grid(row=4, column=0,columnspan=3, sticky="ewns", padx=2, pady=2)

btn_show = Button(frame_menu, text="Show average", command=func_show)
btn_show.grid(row=5, column=0, sticky="ewns", padx=2, pady=2)

btn_expplot = Button(frame_menu, text="Export plot")
btn_expplot.grid(row=5, column=1, sticky="ewns", padx=2, pady=2)

btn_exptable = Button(frame_menu, text="Export table")
btn_exptable.grid(row=5, column=2, sticky="ewns", padx=2, pady=2)

lbl_IRplt = Label(frame_menu,text="Room IR plot:")
lbl_IRplt.grid(row=6, column=0, sticky="ens",pady=2)

cmbx_IRplt = Combobox(frame_menu)
cmbx_IRplt.grid(row=6, column=1, columnspan=2, sticky="wns", pady=2, padx=2)

lbl_bandplt = Label(frame_menu,text="Band:")
lbl_bandplt.grid(row=7, column=0, sticky="ens", pady=2)

cmbx_bandplt = Combobox(frame_menu)
cmbx_bandplt.grid(row=7, column=1, columnspan=2, sticky="wns", pady=2, padx=2)

frame_IRs = Frame(frame_menu)
frame_IRs.grid(row=3, column=0, columnspan=3, sticky="ewns", padx=2, pady=2)
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
frame_settings.grid(row=0, column=1, columnspan=2, rowspan=3, sticky="ewns", padx=2, pady=2)

lbl_settings = Label(frame_settings, text="Settings", anchor="center")
lbl_settings.grid(row=0, column=0,columnspan=2, sticky="ewns")

lbl_bandfilter = Label(frame_settings, text="Band filter:", anchor="e")
lbl_bandfilter.grid(row=1, column=0, sticky="ewns")

cmbx_bandfilter = Combobox(frame_settings, values=("Octave","Third"), state="readonly", width=10)
cmbx_bandfilter.current(1)
cmbx_bandfilter.grid(row=1, column=1, sticky="ewns", pady=1)

lbl_envelope = Label(frame_settings, text="Envelope:", anchor="e")
lbl_envelope.grid(row=2, column=0, sticky="ewns")

cmbx_envelope = Combobox(frame_settings, values=("Schoreder","Median MF","Mean MF"), state="readonly", width=10)
cmbx_envelope.current(0)
cmbx_envelope.bind("<<ComboboxSelected>>",hidesettings)
cmbx_envelope.grid(row=2, column=1, sticky="ewns", pady=1)

lbl_winlen = Label(frame_settings, text="Window lenght:", anchor="e")
lbl_winlen.grid(row=3, column=0, sticky="ewns")
lbl_winlen.grid_remove()

ent_winlen = Entry(frame_settings,width=10)
ent_winlen.grid(row=3, column=1, sticky="ewns",pady=1)
ent_winlen.grid_remove()

lbl_chunk = Label(frame_settings, text="IR chunk:", anchor="e")
lbl_chunk.grid(row=3, column=0, sticky="ewns")

cmbx_chunk = Combobox(frame_settings, values=("Lundeby", "Pepino", "K0"), state="readonly", width=10)
cmbx_chunk.current(0)
cmbx_chunk.grid(row=3, column=1, sticky="ewns", pady=1)

reversedcheck = IntVar()
chkbtn_reverse = Checkbutton(frame_settings, text="Reversed Filtering", variable=reversedcheck)
chkbtn_reverse.grid(row=4, column=0, columnspan=2, sticky="ewns")

frame_table1 = Frame(APC)
frame_table1.grid(row=1,column=0,columnspan=2,padx=4,pady=4,sticky="ewns")
frame_table1.grid_remove()
for i in range(len(filas1)+1):
    for j in range(len(bands_labels[1])+1):
        if i==0 and j!=0:
            table1[i] = table1[i] + [Label(frame_table1, text=bands_labels[1][j-1], bg="white", relief="solid",borderwidth=1)]
            table1[i][j].grid(row=i,column=j,sticky="ewns")
            frame_table1.columnconfigure(j, weight=1)
        elif i!=0 and j==0:
            table1 = table1 + [[Label(frame_table1,text=filas1[i-1], bg="white", relief="solid",borderwidth=1)]]
            table1[i][j].grid(row=i,column=j,sticky="ewns")
        elif i!=0 and j!=0:
            table1[i] = table1[i] + [Label(frame_table1,text="", bg="white", relief="solid",borderwidth=1)]
            table1[i][j].grid(row=i,column=j,sticky="ewns")
        elif i==0 and j==0:
            table1=[[Combobox(frame_table1, values=parameters, width=5, state="readonly")]]
            table1[i][j].current(0)
            table1[i][j].grid(row=i, column=j, sticky="ewns")

frame_table2 = Frame(APC)
frame_table2.grid(row=1,column=0,columnspan=2,padx=4,pady=4,sticky="ewns")
for i in range(len(parameters)+1):
    for j in range(len(bands_labels[1])+1):
        if i==0 and j!=0:
            table2[i] = table2[i] + [Label(frame_table2, text=bands_labels[1][j-1], bg="white", relief="solid",borderwidth=1)]
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