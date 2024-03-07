#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

import tkinter as tk
import tk_tools
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
from datetime import timedelta

#https://stackoverflow.com/questions/603852/how-do-you-udp-multicast-in-python
MCAST_GRP = '224.0.0.1'
MCAST_PORT = 50001
IS_ALL_GROUPS = True
gAni = None

class ApachiTelem:
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
        self.root.title("Apachi Telemetry")
        self.root.geometry("750x450+700+100")

        self.posState = tk.Label(self.root,anchor="w")
        self.posState.grid(column=col,row=row, sticky="w")
        self.altState = tk.Label(self.root,anchor="w")
        self.altState.grid(column=midCol,row=row, sticky="w")
        self.hState = tk.Label(self.root,anchor="w")
        self.hState.grid(column=rtCol,row=row, sticky="w")
        row = 1
        self.dist = tk.Label(self.root, anchor="w")
        self.dist.grid(column=col,row=row, sticky="w")
        self.elTime = tk.Label(self.root, anchor="w")
        self.elTime.grid(column=midCol,row=row, sticky="w")
        self.vState = tk.Label(self.root,anchor="w")
        self.vState.grid(column=rtCol,row=row, sticky="w")
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
        self.fuel = tk.Label(self.root,anchor="w")
        self.fuel.grid(column=midCol,row=row, sticky="w")
        row = 6
        self.dbg1 =  tk.Label(self.root,anchor="w")
        self.dbg1.grid(column=col,row=row, columnspan=3, sticky="w")
        row = 7
        self.dbg2 =  tk.Label(self.root,anchor="w")
        self.dbg2.grid(column=col,row=row, columnspan=3, sticky="w")
        row = 8
        self.fuelG = tk_tools.Gauge(self.root, label="FUEL", max_value=100.1, unit="%",red_low=20.0, yellow_low=30.0,  min_value=0.0, red=100.0, yellow=100.0)
        self.fuelG.grid(column=col,row=row, sticky="w")
        self.spdG = tk_tools.Gauge(self.root, label="SPEED", unit="u/s", max_value=0.1, min_value=-0.1,red=100.0,yellow=100.0)
        self.spdG.grid(column=midCol,row=row, sticky="w")
        self.altG = tk_tools.Gauge(self.root, label="ALT",unit="Ft", min_value=-1.0, max_value=200.0, red_low=2.0,yellow_low=20.0, red=100.0, yellow=100.0)
        self.altG.grid(column=rtCol,row=row, sticky="w")
        

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
            case 1: statStr = "ON GROUND"
            case 2: statStr = "CHANGE ALT"
            case 3: statStr = "AT ALT"
            case 4: statStr = "UP DECEL"
            case 5: statStr = "AT ALT"
            case 6: statStr = "DONW ACCEL"
            case 7: statStr = "DOWN LIN"
            case 8: statStr = "DOWN DECEL"
            case 9: statStr = "TAKE OFF"
            case 20:statStr = "AT HEADING"
            case 21:statStr = "TURNING"
            case 22:statStr = "TURN_LOCK"
            case 30:statStr = "MAINTAIN SPD"
            case 31:statStr = "CHANGE VEL"
            case 32:statStr = "DRIFTING"
            case 100:statStr = "STARTING"
            case 101:statStr = "ON GROUND"
            case 102:statStr = "ALT CHANGE"
            case 103:statStr = "TURNING"
            case 104:statStr = "ACCEL"
            case 105:statStr = "APPROACH"
            case 106:statStr = "DECEL"
            case 110:statStr = "HOVER"
            case 107:statStr = "DECEND"
            case 108:statStr = "LANDED"
            case 109:statStr = "DELIVER"
            case 111:statStr = "TEST"
        return f"{which:<11}: {statStr:<33}"

          
    def parseAndDisplay(self):
        try:
            while not self.queue.empty():
                if self.quit: break
                msg = self.queue.get()
                stI = msg.find(">")
                dI = msg.find("dist:")
                fI = msg.find("facing:")
                elT = msg.find("elapsed:")
                altDes = msg.find("desRS:") #in heading state
                accI = msg.find("velaccel:")
                accSpdI = msg.find("velactT") #in velocity state
                altStI = msg.find("alttrg:") #in altitude state
                altI = msg.find("ApachiAltPID")
                velSpdI = msg.find("velspd:")
                pkgI = msg.find("packages: ")
                dbg1 = msg.find("DEBUG1:")
                dbg2 = msg.find("DEBUG2:")
                headI = msg.find("ApachiHeadPID")
                fuelI = msg.find("REMFUEL")
                floatVal1 = None; fact1 = None
                floatVal2 = None; fact2 = None
                floatVal3 = None; fact3 = None
                floatVal4 = None; fact4 = None
                if pkgI >= 0:
                    self.pkgs["text"] = self.getData("packages: ",msg,",")
                if fuelI >= 0:
                    fStr = self.getData("REMFUEL:",msg,",","FUEL: ")
                    self.fuel["text"] = fStr
                    try:
                        ms = RegEx.match(".*\((.*)%.*",fStr)
                        if ms is not None and ms.group(1) is not None:
                            self.fuelG.set_value(float(ms.group(1)))
                    except: pass
                if dI >= 0 and fI >=0:
                    self.dist["text"] = self.getData("dist:",msg,',',"DISTANCE:")
                    self.face["text"] = self.getData("facing:",msg)
                    self.head["text"] = self.getData("head:",msg)
                    self.speed["text"] = self.getData("speed:",msg)
                    self.spdG.set_value(10.0 * self.getDatFloat("speed:",msg,","))
                    statStr = msg[:(stI)]
                    self.posState["text"] = self.str2State("POS STATE",statStr)
                    self.cp["text"] = self.getData("cur   :",msg,"|","CUR POS:")
                    self.ap["text"] = self.getData("trg   :",msg,"|","TRG POS:")
                    self.headTrg["text"] = self.getData("trgHdg:",msg," [","TRG HGD:")
                if accI >= 0 and accSpdI >= 0:
                      self.accel["text"] = self.getData("accel:",msg)
                      state = msg[:stI]
                      self.vState["text"] = self.str2State("VEL STATE",state)
                if elT >= 0 and altDes >= 0:
                      state = msg[:stI]
                      self.hState["text"] = self.str2State("HDG STATE",state)
                      secsFlt = self.getDatFloat("elapsed:",msg,",")
                      secsInt = int(secsFlt)
                      secFmtStr = str(timedelta(seconds = secsInt))
                      self.elTime["text"] = f"Elapsed: {secFmtStr:>08}"
                if altI >= 0:
                    state = msg[:stI]
                    self.altState["text"] = self.str2State("ALT STATE",state)
                    self.alt["text"] = self.getData("altact:",msg,",","alt:") + "/" + self.getData("alttrg:",msg,",","") 
                    self.altG.set_value(1.0 * self.getDatFloat("altact:",msg,","))
                    self.accel["text"] = self.getData("altaccel:",msg,",","ALT ACCEL:")
                if False: #velSpdI >= 0: #velocity
                    floatVal1 = self.getDatFloat("veltrg:",msg,","); fact1 = 100.0 #trg speed yellow
                    floatVal2 = self.getDatFloat("velspd:",msg,","); fact2 = 100.0 #act speed green
                    floatVal3 = self.getDatFloat("err:",msg,","); fact3 = 100.0 #vel error red 
                    floatVal4 = self.getDatFloat("velactT:",msg,","); fact4 = .10 #tilt blue
                if False: #headI >= 0: #heading graphs
                    floatVal1 = self.getDatFloat("trg: ",msg,","); fact1 = 0.1
                    floatVal2 = self.getDatFloat("act: ",msg,","); fact2 = 0.1
                    floatVal3 = self.getDatFloat("actRotSpd: ",msg,","); fact3 = 0.03
                    floatVal4 = self.getDatFloat("dA: ",msg,","); fact4 = 5.0
                if altI >= 0: #altitude
                    floatVal1 = self.getDatFloat("alttrg: ",msg,","); fact1 = 0.1
                    floatVal2 = self.getDatFloat("altact: ",msg,","); fact2 = 0.1
                    floatVal3 = self.getDatFloat("act rot: ",msg,","); fact3 = 0.03
                    floatVal4 = self.getDatFloat("error: ",msg,","); fact4 = 1.0
                    
                if dbg1 >= 0:
                    self.dbg1["text"] = self.getData("DEBUG1:",msg)
                if dbg2 >= 0:
                    self.dbg2["text"] = self.getData("DEBUG2:",msg)
                added = False
                if floatVal1 is not None:
                    self.ydata1.append(floatVal1 * fact1); added = True
                if floatVal2 is not None:
                    self.ydata2.append(floatVal2 * fact2); added = True
                if floatVal3 is not None:
                    self.ydata3.append(floatVal3 * fact3); added = True
                if floatVal4 is not None:
                    self.ydata4.append(floatVal4 * fact4); added = True
                if added:
                    self.xdata.append(datetime.datetime.now())

                #self.lbl1["text"] = self.queue.get()
        except Exception as ex:
            print(f"Unable to set data to label: {ex}")
        
        while len(self.xdata) > 6000:
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