from queue import *

scenario =2


sched=scheduler(tick=0.001,finish=10)

traf=trafgen('traf',ms1=1)
term2=terminal('term2')

if scenario == 0:
  connect('con1',traf.B,term2.A)
elif scenario == 1:
  node1=duplex('node1')
  connect('con1',traf.B,node1.A)
  connect('con2',term2.A,node1.B)
elif scenario == 2:
  stack1 = stack('stack1')
  stack2 = stack('stack2')
  connect('linkA',traf.B,stack1.A)
  connect('linkB',stack1.B,stack2.A)
  connect('linkC',stack2.B,term2.A)

sched.process()

