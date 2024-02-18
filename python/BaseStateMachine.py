#!/usr/bin/python3

# (c) 2015-2024, A Beloussov, D. Lafuze

import queue
import inspect
import time


class BaseStateMachine:

    TAG = "BaseStateMachine"
    DBG_MASK = 0x4

    INIT_ST = 0
    ERROR_ST = 1

    NULL_EVT = 0
    DONE_EVT = 1
    RESET_EVT = 2
    ERROR_EVT = 3

    leave = None
    handle = None

    dt = 0
    lastStamp = time.time_ns()
    eventQ = queue.Queue()
    lastChange = lastStamp
    state = INIT_ST
    firstTick = True

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
        self.db("Initialied Generic State Machine")
        self.TAG = TAG
        self.DBG_MASK = DBG

    def sendEvent(self,evt):
        self.eventQ.put(evt)
        
    def next(self):
        while not self.eventQ.empty():
            evt = self.eventQ.get()
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