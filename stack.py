from queue import *

sched=scheduler(tick=0.001,finish=10)

node1=duplex('node1')
stack1 = stack('stack1')
stack2 = stack('stack2')


traf=trafgen('traf')
term2=terminal('term2')

connect('linkA',traf.B,stack1.A)
connect('linkB',stack1.B,stack2.A)
connect('linkC',stack2.B,term2.A)

sched.process()

