from queue import *

sched=scheduler(tick=0.001,finish=10)

traf=trafgen('traf',ms1=1)
# sched.addp(traf.worker1,0.000,0.100)

term2=terminal('term2')

connect('con1',traf.B,term2.A)

sched.process()

