#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

import tkinter as tk
import socket
import struct
from threading import Thread
import queue
import re as RegEx

#https://stackoverflow.com/questions/603852/how-do-you-udp-multicast-in-python
MCAST_GRP = '224.1.1.1'
MCAST_PORT = 50001
IS_ALL_GROUPS = True

class ApachiTelem:
    sock = None
    root = None
    queue = queue.Queue()
    thread = None
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
        self.root.geometry("750x450")

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
        self.accel.grid(column=midCol,row=row-1, sticky="w")
        row = 4
        self.cp = tk.Label(self.root,anchor="w")
        self.cp.grid(column=col,row=row, sticky="w")
        row = 5
        self.ap = tk.Label(self.root,anchor="w")
        self.ap.grid(column=col,row=row, sticky="w")
        row = 6

        print(f"GUI Created...")

    def recvThread(self):
        print(f'Starting to receive telemetry')
        while True:
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

    def str2State(self, which, statStr):
        match(int(statStr)):
            case 1: statStr = "ON GROUND"
            case 2: statStr = "UP ACCEL"
            case 3: statStr = "UP LIN"
            case 4: statStr = "UP DECEL"
            case 5: statStr = "AT ALT"
            case 6: statStr = "DONW ACCEL"
            case 7: statStr = "DOWN LIN"
            case 8: statStr = "DOWN DECEL"
            case 9: statStr = "TAKE OFF"
            case 20:statStr = "AT HEADING"
            case 21:statStr = "TURN_KICK"
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
            case 110:statStr = "TEST"
        return f"{which:<11}: {statStr:<33}"

          
    def parseAndDisplay(self):
        try:
            while not self.queue.empty():
                msg = self.queue.get()
                stI = msg.find(">")
                dI = msg.find("dist:")
                fI = msg.find("facing:")
                altI = msg.find("elapsed:")
                altDes = msg.find("desRS:") #in heading state
                accI = msg.find("accel:")
                accSpdI = msg.find("actT") #in velocity state
                altStI = msg.find("exp rt:") #in altitude state
                if dI >= 0 and fI >=0:
                    self.dist["text"] = self.getData("dist:",msg,',',"DISTANCE:")
                    self.face["text"] = self.getData("facing:",msg)
                    self.head["text"] = self.getData("head:",msg)
                    self.speed["text"] = self.getData("speed:",msg)
                    statStr = msg[:(stI)]
                    self.posState["text"] = self.str2State("POS STATE",statStr)
                    self.cp["text"] = self.getData("cur   :",msg,"|","CUR POS:")
                    self.ap["text"] = self.getData("trg   :",msg,"|","TRG POS:")
                    self.headTrg["text"] = self.getData("trgHdg:",msg," [","TRG HGD:")
                if accI >= 0 and accSpdI >= 0:
                      self.accel["text"] = self.getData("accel:",msg)
                      state = msg[:stI]
                      self.vState["text"] = self.str2State("VEL STATE",state)
                if altI >= 0 and altDes >= 0:
                      state = msg[:stI]
                      self.hState["text"] = self.str2State("HDG STATE",state)
                      self.elTime["text"] = self.getData("elapsed:",msg,",","elapsed:")
                if altStI >= 0:
                    state = msg[:stI]
                    self.altState["text"] = self.str2State("ALT STATE",state)
                

                #self.lbl1["text"] = self.queue.get()
        except Exception as ex:
            print(f"Unable to set data to lable: {ex}")
        self.root.after(100, self.parseAndDisplay)

    def startThread(self):
        self.thread = Thread(target = self.recvThread,daemon=True)
        self.thread.start()


if __name__ == "__main__":
    recv = ApachiTelem()
    recv.parseAndDisplay()
    recv.startThread()
    print(f"Strting MAIN LOOP")
    recv.root.mainloop()
    recv.sock.close()