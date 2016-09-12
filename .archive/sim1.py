from queue import *

sched=scheduler(tick=0.001,finish=10)

stack1 = stack('stack1')
stack2 = stack('stack2')

traf=trafgen('traf')
# sched.addp(traf.worker1,0.000,0.100)
term2=terminal('term2')

connect('linkA',traf.B,stack1.A)
connect('linkB',stack1.B,stack2.A)
connect('linkC',stack2.B,term2.A)

sched.process()

