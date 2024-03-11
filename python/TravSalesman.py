import threading
import itertools
import math
import os
from multiprocessing import Process
import multiprocessing as mp
import time
import numpy as np
import gc

from panda3d.core import Vec2, Vec3


class TravSalesman:
    wps = []
    DBG_MASK = 0x20
    TAG = "TravSalesman"
    idx = []
    done = False
    stop = False
    curPos = Vec3(0, 0, 0)
    cp2 = None
    used = set()
    lowScore = 1e9
    lowScoreCombo = None
    thrHndls = []
    numThreads = 1
    curIdx = 0


    def __init__(self):
        self.numThreads = int(os.cpu_count() * 0.9)
        self.queue = None
        self.lowScores = []
        self.lowScoreCombos = []
        self.curIdx = 0
        for _ in range(0,self.numThreads):
            self.lowScores.append(1e9)
            self.lowScoreCombos.append(None)

    def calcScore(self, preHdg, p1, p2):
        diff = (p1 - p2)
        trgHdg = math.atan2(diff.y,diff.x)
        hdg = abs(trgHdg - preHdg)
        dist = diff.length()
        score = hdg / 16.2 + dist / 550.0
        if dist > 310.0:
            score *= 1.7
        elif dist < 36.0:
            score *= 0.7
        return trgHdg, score

    def calcTotalScore(self, combo3, lowScore):
        combo = []
        for ptIdx in combo3:
            cmb = self.wps[ptIdx]
            combo.append(cmb.xy)
        preHdg, score = self.calcScore(0.0, self.cp2,combo[0])
        if score < lowScore:
            for i in range(0,len(combo) - 1):
                preHdg, sc = self.calcScore(preHdg, combo[i], combo[i+1])
                score += sc
                if score >= lowScore: break
        del combo
        return score
    
    def determine(self, curPos, wps):
        self.done = False
        self.curPos = curPos
        self.cp2 = curPos.xy
        self.wps = wps
        self.__init__()
        self.thrHndls = []
        sz = len(wps)
        self.queue = mp.Queue()
        for i in range(0,self.numThreads):
            self.thrHndls.append(Process(target=self.proc_calculate,args=(i,sz,self.numThreads,self.queue)))
            self.thrHndls[-1].start()

    def proc_calculate(self,idx,sz,mx,queue):
        #print(f"Thread {idx}, processing {len(lst):,} entries ")
        then = time.time_ns()
        idxArr = np.arange(sz,dtype=np.int8)
        allItr = itertools.permutations(idxArr,len(idxArr))
        lowScore = 1e9
        lowCombo = None
        num = 0
        cnt = 0
        for combo in allItr:
            if (num % mx) == idx:
                score = self.calcTotalScore(combo,lowScore)
                cnt += 1
                #print(f"Scoore: {score} for {combo}                   ",end='\r')
                if score < lowScore:
                    lowScore = score
                    lowCombo = combo
            num += 1
        queue.put((lowScore,lowCombo))
        now = time.time_ns()
        dt = (now - then) * 1e-9
        #print(f"Thread {idx} ========= DONE: low score {lowScore}, combo: {lowCombo}; proc {cnt:,} entries in {dt: >.2f} secs")

    def allDone(self):
        allDone = True
        for t in self.thrHndls:
            if t.is_alive():
                allDone = False
                break
        return allDone

    def finish(self):
        #print(f"Waiting for all to be done")
        if not self.done:
            while(not self.allDone()):
                pass
            self.lowScore = 1e9
            idx = 0
            while not self.queue.empty():
                sc, combo = self.queue.get()
                #print(f" New low score of {sc} with {combo}")
                if sc < self.lowScore:
                    self.lowScore = sc
                    self.lowScoreCombo = combo
                idx += 1
            self.idx = self.lowScoreCombo
            #print("")
            #print(f"====== the lowest score of {self.lowScore} of {self.lowScoreCombo}")
            #print(f" Indexes: {self.idx}")
            self.done = True

    def nextIndex(self):
        idx = self.curIdx
        if idx >= len(self.idx): return None
        self.curIdx += 1
        return self.idx[idx]

if __name__ == '__main__':
    sm = TravSalesman()
    curPos = Vec3(60.0, 10.0, 0.0)
    wps = []
    wps.append(Vec3(-165.0, 10.0, 0.0))
    wps.append(Vec3(-240.0, -240.0, 0.0))
    wps.append(Vec3(-140.0, 10.0, 0.0))
    wps.append(Vec3(-115.0, 35.0, 0.0))
    wps.append(Vec3(60.0, -240.0, 0.0))
    wps.append(Vec3(85.0, -265.0, 0.0))
    wps.append(Vec3(135.0, 10.0, 0.0))
    wps.append(Vec3(-215.0, 210.0, 0.0))
    wps.append(Vec3(135.0, 160.0, 0.0))
    wps.append(Vec3(-65.0, -165.0, 0.0)) #completes in 9 secs
    #wps.append(Vec3(-15.0, -140.0, 0.0)) #1.3min
    #wps.append(Vec3(-140.0, 210.0, 0.0)) #19.9 min
    '''
    wps.append(Vec3(-265.0, 210.0, 0.0))
    wps.append(Vec3(-90.0, -15.0, 0.0))
    wps.append(Vec3(135.0, -165.0, 0.0))
    '''
    res = sm.determine(curPos,wps)
    for t in sm.thrHndls:
        t.join()
    sm.finish()

