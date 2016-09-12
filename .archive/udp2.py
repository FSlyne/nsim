from network import *

sched=scheduler(tick=0.001,finish=10)

udp = udp_stack('ip_stack1',based=True)

traf=trafgen('traf')
term2=terminal('term2')

connect('con1',traf.B,udp.D)
connect('con2',term2.A,udp.C)

sched.process()
