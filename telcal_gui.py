#! /usr/bin/env python

# Simple TK-based GUI for plotting TelCal results.
# P. Demorest, 2017/03

import os, glob, string
import time

import numpy as np
import matplotlib
matplotlib.use('TkAgg')
#import matplotlib.pyplot
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, 
        NavigationToolbar2TkAgg)
#from matplotlib.backend_bases import key_press_handler # need?
from matplotlib.figure import Figure

import Tkinter as tk
import ttk
import telcal

class TelcalGUI(object):

    def __init__(self, parent):

        parent.title('Telcal Plotter')

        self.parent = parent
        self.outerF = tk.Frame(parent,padx=5,pady=5)
        self.outerF.pack()

        # Put control frame in place
        self.controlF = ttk.LabelFrame(self.outerF,text='Dataset')
        self.controlF.pack(side=tk.LEFT,fill=tk.Y,expand=1)

        # Date controls
        t = time.localtime()
        self.dateF = ttk.Frame(self.controlF)
        self.dateF.pack(side=tk.TOP,anchor=tk.W,fill=tk.X)
        self.year = tk.StringVar(value='%04d'%t.tm_year)
        self.month = tk.StringVar(value='%02d'%t.tm_mon)
        self.basedir = telcal.telcaldir
        self.yearE = ttk.Entry(self.dateF,width=4,textvariable=self.year)
        self.yearE.pack(side=tk.LEFT)
        self.monthE = ttk.Entry(self.dateF,width=2,textvariable=self.month)
        self.monthE.pack(side=tk.LEFT)

        # Glob
        self.glob = tk.StringVar(value='*')
        self.globE = ttk.Entry(self.dateF,width=32,textvariable=self.glob)
        self.globE.pack(side=tk.LEFT,fill=tk.X,expand=1)

        self.reloadB = ttk.Button(self.dateF,text='Apply',
                command=self.refresh_dataset_list)
        self.reloadB.pack(side=tk.LEFT)

        # Filename list
        self._datasetlist = tk.StringVar()
        self.refresh_dataset_list()
        self.datasetF = ttk.Frame(self.controlF)
        self.datasetF.pack(side=tk.TOP,fill=tk.Y,expand=1)
        self.datasetS = ttk.Scrollbar(self.datasetF)
        self.datasetS.pack(side=tk.RIGHT,fill=tk.Y)
        self.datasetL = tk.Listbox(self.datasetF,width=48,
                yscrollcommand=self.datasetS.set,
                selectmode=tk.SINGLE,
                listvariable=self._datasetlist,
                exportselection=0)
        self.datasetL.pack(fill=tk.Y,expand=1)
        self.datasetL.activate(0)
        self.datasetS.config(command = self.datasetL.yview)

        # Control buttons
        self.buttonF = ttk.Frame(self.controlF)
        self.buttonF.pack(side=tk.TOP)
        self.plotB = ttk.Button(self.buttonF,text='Plot',
                command=self.update_plot)
        self.plotB.pack(side=tk.LEFT)

        self.datasetL.bind('<Double-1>', lambda x: self.plotB.invoke())

        # Data selection area
        self.dataF = ttk.LabelFrame(self.outerF,text='Ant')
        self.dataF.pack(side=tk.LEFT,anchor=tk.N)

        self._antennalist = tk.StringVar()
        #self._antennalist.set(string.join(
        #    map(lambda x: 'ea%02d'%x, range(1,29)), ' '))
        self._antennalist.set('all')
        self.antL = tk.Listbox(self.dataF, width=4, height=29,
                listvariable=self._antennalist,
                selectmode=tk.BROWSE,
                exportselection=0)
        self.antL.bind('<<ListboxSelect>>', lambda x: self.update_plot())
        self.antL.activate(0)
        self.antL.pack()

        # Put plot frame in place
        self.plotF = ttk.Frame(self.outerF)
        self.plotF.pack(side=tk.LEFT)

        # Add figure..
        self.plotfig = Figure(figsize=(10,5))
        self.axes = {}
        self.axes['AT'] = self.plotfig.add_subplot(321)
        self.axes['AF'] = self.plotfig.add_subplot(322,sharey=self.axes['AT'])
        self.axes['DT'] = self.plotfig.add_subplot(323,sharex=self.axes['AT'])
        self.axes['DF'] = self.plotfig.add_subplot(324,sharex=self.axes['AF'],
                sharey=self.axes['DT'])
        self.axes['PT'] = self.plotfig.add_subplot(325,sharex=self.axes['AT'])
        self.axes['PF'] = self.plotfig.add_subplot(326,sharex=self.axes['AF'],
                sharey=self.axes['PT'])


        self.plotcanvas = FigureCanvasTkAgg(self.plotfig, master=self.plotF)
        self.plotcanvas.show()
        self.plotcanvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH,
                expand=1)
        self.plottoolbar = NavigationToolbar2TkAgg(self.plotcanvas, self.plotF)
        self.plottoolbar.update()
        self.plotcanvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)


        self._dsloaded = None
        self.data = None

    @property
    def datadir(self):
        return os.path.join(self.basedir, self.year.get(), self.month.get())

    @property
    def filelist(self):
        return sorted(glob.glob(self.datadir + '/%s.GN'%self.glob.get()),
                key=os.path.getmtime, reverse=True)

    @property
    def datasets(self):
        return map(lambda x: os.path.splitext(os.path.basename(x))[0],
                self.filelist)

    def refresh_dataset_list(self):
        self._datasetlist.set(string.join(self.datasets,' '))

    @property
    def curselection(self):
        idx = self.datasetL.curselection()
        if len(idx)==0: return None
        return self.datasetL.get(idx[0])

    @property
    def antselection(self):
        idx = self.antL.curselection()
        if len(idx)==0: return None
        out = []
        for i in idx:
            out.append(self.antL.get(i))
        return out

    def load_telcal(self):
        # Load the telcalDB from the current selection
        self._dsloaded = self.curselection
        self.data = telcal.TelcalDB(
                '%s/%s/%s.GN' % (self.year.get(), self.month.get(), 
                    self._dsloaded),
                basedir=self.basedir)

    def plotids(self):
        return np.core.defchararray.add(self.curdat.ant,
                np.array(map(lambda x: x.split('-')[0], self.curdat.ifid)))

    def update_freq_plot(self,axes):
        tlim = axes.get_xlim()
        fplots = ('AF', 'DF', 'PF')
        for p in fplots: self.axes[p].clear()
        ids = self.plotids()
        tt = 24.0*(self.curdat.mjd-self.t0)
        for k in sorted(list(set(ids))):
            idx = np.where((ids==k)*(tt>tlim[0])*(tt<tlim[1]))
            ff = self.curdat.freq[idx] / 1e3
            #si = np.argsort(ff)
            self.axes['PF'].plot(ff, (self.curdat.phase[idx]), '+')
            self.axes['DF'].plot(ff, (self.curdat.delay[idx]), '+')
            self.axes['AF'].plot(ff, (self.curdat.amp[idx]), '+')
        self.axes['PF'].set_xlabel('Freq (GHz)')

        for p in fplots:
            self.axes[p].grid(True)
            self.axes[p].yaxis.tick_right()

        for p in ('AF', 'DF'):
            for l in self.axes[p].get_xticklabels():
                l.set_visible(False)

    def update_time_plot(self,axes=None):
        if axes is not None:
            flim = axes.get_xlim()
        else:
            flim = None
        tplots = ('AT', 'DT', 'PT')
        for p in tplots: self.axes[p].clear()
        ids = self.plotids()
        ff = self.curdat.freq / 1e3
        for k in sorted(list(set(ids))):
            if flim is None:
                idx = np.where(ids==k)
            else:
                idx = np.where((ids==k)*(ff>flim[0])*(ff<flim[1]))
            tt = 24.0*(self.curdat.mjd[idx]-self.t0)
            self.axes['PT'].plot(tt, self.curdat.phase[idx], '+')
            self.axes['DT'].plot(tt, self.curdat.delay[idx], '+')
            self.axes['AT'].plot(tt, self.curdat.amp[idx], '+')
        self.axes['PT'].set_xlabel('Time (UT; h)')

        self.axes['AT'].set_ylabel('Amp')
        self.axes['DT'].set_ylabel('Delay (ns)')
        self.axes['PT'].set_ylabel('Phase (deg)')

        for p in tplots:
            self.axes[p].grid(True)

        for p in ('AT', 'DT'):
            for l in self.axes[p].get_xticklabels():
                l.set_visible(False)

    def update_plot(self):
        if self.curselection is not None:
            if self.curselection != self._dsloaded:
                self.load_telcal()
                self._antennalist.set('all ' + string.join(self.data.ants,' '))
                self.antL.activate(0)
        for p in self.axes.values(): p.clear()
        if (self.antselection is None) or ('all' in self.antselection):
            self.curdat = self.data.get()
        else:
            self.curdat = self.data.get(ants=self.antselection)
        if len(self.curdat.mjd)==0: return
        self.t0 = int(self.curdat.mjd.min())

        self.update_time_plot()
        self.update_freq_plot(self.axes['AT'])

        self.axes['PT'].set_ylim((-180,180))

        self.plotfig.tight_layout()

        for p in ('AT', 'DT', 'PT'):
            self.axes[p].callbacks.connect('xlim_changed', 
                    self.update_freq_plot)

        for p in ('AF', 'DF', 'PF'):
            self.axes[p].callbacks.connect('xlim_changed', 
                    self.update_time_plot)

        self.plotfig.subplots_adjust(hspace=0.01,wspace=0.01)
        self.plotcanvas.show()

if __name__ == '__main__':
    root = tk.Tk()
    telcalgui = TelcalGUI(root)
    root.mainloop()
