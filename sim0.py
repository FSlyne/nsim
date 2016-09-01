from queue import *

sched=scheduler(tick=0.001,finish=10)

node1=duplex('node1')

traf=trafgen('traf')
sched.addp(traf.worker1,0.000,0.100)

term2=terminal('term2')

connect('con1',traf.B,node1.A)
connect('con2',term2.A,node1.B)

sched.process()

