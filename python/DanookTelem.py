#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

import tkinter as tk
import socket
import struct
from threading import Thread
import queue
import re as RegEx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import datetime
import math
import random

#https://stackoverflow.com/questions/603852/how-do-you-udp-multicast-in-python
MCAST_GRP = '224.0.0.1'
MCAST_PORT = 50002
IS_ALL_GROUPS = True
gAni = None

class DanookTelem:
    sock = None
    root = None
    queue = queue.Queue()
    thread = None
    quit = False
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if IS_ALL_GROUPS:
            # on this port, receives ALL multicast groups
            self.sock.bind(('', MCAST_PORT))
        else:
            # on this port, listen ONLY to MCAST_GRP
            self.sock.bind((MCAST_GRP, MCAST_PORT))
        self.mreq = struct.pack("4sl", socket.inet_aton(MCAST_GRP), socket.INADDR_ANY)

        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, self.mreq)

        print(f" socket created {self.sock}")
        row = 0
        col = 0
        midCol = 1
        rtCol = 2
        self.root = tk.Tk()
        self.root.title("Danook Telemetry")
        self.root.geometry("750x450+700+100")

        self.state = tk.Label(self.root,anchor="w")
        self.state.grid(column=col,row=row, sticky="w")
        row = 1
        self.dist = tk.Label(self.root, anchor="w")
        self.dist.grid(column=col,row=row, sticky="w")
        self.elTime = tk.Label(self.root, anchor="w")
        self.elTime.grid(column=midCol,row=row, sticky="w")
        row = 2
        self.face = tk.Label(self.root,anchor="w")
        self.face.grid(column=col,row=row, sticky="w")
        self.head = tk.Label(self.root,anchor="w")
        self.head.grid(column=midCol,row=row, sticky="w")
        self.headTrg = tk.Label(self.root,anchor="w")
        self.headTrg.grid(column=rtCol,row=row, sticky="w")
        row = 3
        self.speed = tk.Label(self.root,anchor="w")
        self.speed.grid(column=col,row=row, sticky="w")
        self.accel = tk.Label(self.root,anchor="w")
        self.accel.grid(column=midCol,row=row, sticky="w")
        self.alt = tk.Label(self.root,anchor="w")
        self.alt.grid(column=rtCol,row=row, sticky="w")
        row = 4
        self.cp = tk.Label(self.root,anchor="w")
        self.cp.grid(column=col,row=row, sticky="w")
        self.pkgs = tk.Label(self.root,anchor="w")
        self.pkgs.grid(column=rtCol,row=row,sticky="w")
        row = 5
        self.ap = tk.Label(self.root,anchor="w")
        self.ap.grid(column=col,row=row, sticky="w")
        row = 6

        print(f"GUI Created...")
        self.fig, self.ax = plt.subplots()
        self.xdata = []
        self.ydata1 = []
        self.ydata2 = []
        self.ydata3 = []
        self.ydata4 = []
        self.ln1, = plt.plot([], [], "yo") #alt
        self.ln2, = plt.plot([], [], "gx") # rot spd
        self.ln3, = plt.plot([], [], "r+") # vel
        self.ln4, = plt.plot([], [], "b.") # accel
        self.root.protocol("WM_DELETE_WINDOW", self.exitLoop)

    def plotInit(self):
        #self.ax.set_ylim(-1000.0, 1000)
        return self.ln1,

    def recvThread(self):
        print(f'Starting to receive telemetry')
        while True:
            if self.quit: break
            try:
                data, addr = self.sock.recvfrom(1024)
            except socket.error as e:
                print(f"Exception: {e}")
            else:
                dataStr = data.decode()
                self.queue.put(dataStr)
                #print(dataStr)

    def getData(self,key,msg, endCh = ',',cap = None):
          bIdx = msg.find(key)
          eIdx = msg.find(endCh,bIdx+1)
          res = msg[bIdx:eIdx]
          if cap is not None:
            res = RegEx.sub(key,cap,res)
          res = res.upper()
          res = f"{res:<45}"
          return res
    
    def getDatFloat(self,key,msg,endCh = ',',cap = None):
        regEx = f".*{key}(.*?){endCh}.*"
        ms = RegEx.match(regEx,msg)
        if ms is not None:
            valStr = ms.group(1)
        else:
            valStr = "0.001"
            print(f"NOT FOUND msg: {msg}, ms: {ms.group(1)} regex: {regEx}")
        try:
            val = float(valStr)
        except:
            val = 0.0
            print(f"NOT A FLOAT msg: {msg}, ms: {ms.group(1)} regex: {regEx}")
        return val
    

    def str2State(self, which, statStr):
        match(int(statStr)):
            case 1: statStr = "LANDED"
            case 2: statStr = "CLIMB"
            case 3: statStr = "FIND_HEADING"
            case 4: statStr = "STABILIZE_HEADING"
            case 5: statStr = "APPROACHING"
            case 6: statStr = "STOP_NOW"
            case 7: statStr = "TASKS_COMPLETE"
            case 8: statStr = "POWER_DOWN"
        return f"{which:<11}: {statStr:<33}"

          
    def parseAndDisplay(self):
        try:
            while not self.queue.empty():
                if self.quit: break
                msg = self.queue.get()

                #self.lbl1["text"] = self.queue.get()
        except Exception as ex:
            print(f"Unable to set data to label: {ex}")
        
        while len(self.xdata) > 2000:
            self.xdata.pop(0)
            self.ydata1.pop(0)
            self.ydata2.pop(0)
            self.ydata3.pop(0)
            self.ydata4.pop(0)
        if not self.quit:
            self.root.after(100, self.parseAndDisplay)
    
    def plot(self,frame):
        #self.xdata.append(datetime.datetime.now())
        #self.ydata1.append(random.randint(-4,5) )
        self.ln1.set_data(self.xdata,self.ydata1)
        self.ln2.set_data(self.xdata,self.ydata2)
        self.ln3.set_data(self.xdata,self.ydata3)
        self.ln4.set_data(self.xdata,self.ydata4)
        self.fig.gca().relim()
        self.fig.gca().autoscale_view()
        return self.ln1,

    def exitLoop(self):
        self.quit = True
        self.sock.close()
        self.root.quit()
        self.root.destroy()

    def showPlotThr(self):
        #plt.show()
        self.root.mainloop()
        pass

    def startThread(self):
        self.thread = Thread(target = self.recvThread,daemon=True)
        self.thread.start()
        self.ani = FuncAnimation(fig = self.fig, func = self.plot, init_func = self.plotInit, blit=False)
        self.pltThr = Thread(target=self.showPlotThr,daemon=True)
        self.pltThr.start()


if __name__ == "__main__":
    recv = ApachiTelem()
    recv.parseAndDisplay()
    recv.startThread()
    print(f"Strting MAIN LOOP")
    #recv.root.mainloop()
    plt.show()
    print(f"OUT OF MAIN LOOP")