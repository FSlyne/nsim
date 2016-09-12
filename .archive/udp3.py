from network import *

sched=scheduler(tick=0.001,finish=10)

udp1 = udp_stack('udp_stack1')
udp2 = udp_stack('udp_stack2')

router = ip_stack('router',capped=True)

traf=trafgen('traf')
term2=terminal('term2')

connect('con1',traf.B,udp1.D)
connect('con2',term2.A,udp2.C)
connect('con3',udp1.B,router.A)
connect('con4',udp2.A,router.B)

sched.process()
