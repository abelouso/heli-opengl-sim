#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

import queue
import inspect
import time
import socket
import struct

#https://stackoverflow.com/questions/603852/how-do-you-udp-multicast-in-python
MCAST_GRP = '224.0.0.1'
MCAST_PORT = 50001
IS_ALL_GROUPS = True
MULTICAST_TTL = 2

class BaseStateMachine:

    TAG = "BaseStateMachine"
    DBG_MASK = 0x4

    INIT_ST = 0
    ERROR_ST = 1

    NULL_EVT = 0
    DONE_EVT = 1
    RESET_EVT = 2
    ERROR_EVT = 3

    def initHndl(self):
        self.db("In Init state")

    def errHndl(self):
        self.db("In Error state")

    def errEvt(self):
        self.db("Error occured")

    '''
    StateHandlers = {
        INIT_ST: (   None,   initHndl,   None),
        ERROR_ST: (   None,   errHndl,   None),
    }

    StateMachine = {
        INIT_ST: {
            RESET_EVT: (INIT_ST, None),
            DONE_EVT: (INIT_ST, None),
            NULL_EVT: (INIT_ST, None),
            ERROR_EVT: (ERROR_ST, None),
        },
        ERROR_ST: {
            RESET_EVT: (INIT_ST, None),
            DONE_EVT: (ERROR_ST, None),
            NULL_EVT: (ERROR_ST, None),
            ERROR_EVT: (ERROR_ST, None),
        },
    }
    '''
    def __init__(self, TAG, DBG):
        self.db(f"Initialied Generic State Machine for tag {TAG}")
        self.TAG = TAG
        self.DBG_MASK = DBG
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, MULTICAST_TTL)

    def sendEvent(self,evt):
        self.eventQ.put(evt)
        self.db(f"Sent event: {evt}, queue empty: {self.eventQ.empty()}")
        
    def next(self):
        while not self.eventQ.empty():
            evt = self.eventQ.get()
            self.db(f"processing evt: {evt}")
            stMap = self.StateMachine[self.state]
            newState = self.state
            if evt in stMap:
                newState, evtHndl = stMap[evt]
                enter, handle, leave = self.StateHandlers[newState]
                if newState != self.state or self.firstTick:
                    self.db(f"State TX: {self.state}: {evt} -> {newState}")
                    if self.leave is not None:
                        self.leave(self)
                    if evtHndl is not None:
                        evtHndl(self)
                    self.leave = leave
                    if enter is not None:
                        enter(self)
                    self.state = newState
                else:
                    pass
                if handle is not None:
                    handle(self)
                self.handle = handle
                self.firstTick = False

    def tick(self, act, spd, dt):
        self.updateTimeStamp()
        self.next()
        return 0
    
    def updateTimeStamp(self):
        now = time.time_ns()
        dt = (now - self.lastStamp) * 0.00000001 #ns
        self.dt = dt
        self.lastStamp = now

    def db(self, msg):
        calFn = inspect.getouterframes(inspect.currentframe(),2)[1][3]
        msg = f"{self.state}> {msg} [{calFn}]"
        try:
            self.sock.sendto(msg.encode(), (MCAST_GRP, MCAST_PORT))
        except Exception as ex:
            print(f"Exception sendin, {ex}")
        try:
            base.dbg(self.TAG,msg,self.DBG_MASK)
        except:
            print(msg)


if __name__ == "__main__":
    head = BaseStateMachine("TEST", 0x2)
    head.sendEvent(head.NULL_EVT)
    head.tick(100,100,0.1)
    head.tick(100,100,0.1)
    head.sendEvent(head.ERROR_EVT)
    head.tick(100,100,0.1)
    head.sendEvent(head.RESET_EVT)
    head.tick(100,100,0.1)