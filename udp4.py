from network import *

sched=scheduler(tick=0.001,finish=10)

host1=host('host1',stack='udp')
host2=host('host2',stack='udp')

# sw=eth_switch('sw')
sw1=vswitch('sw1',"","Dot1Q()")
sw2=vswitch('sw2',"Dot1Q()","MPLS()")
sw3=vswitch('sw3',"MPLS()","")

link=transmission('link1',latency=40,trace=True)

traf=trafgen('traf',once=1)
term2=terminal('term2')

connect('con1',traf.B,host1.B)
connect('con2',term2.A,host2.B)
connect('con3',host1.A,sw1.A)
connect('con4',sw1.B,sw2.A)
connect('lcon1',sw2.B,link.A)
connect('lcon2',link.B,sw3.A)
connect('con6',sw3.B,host2.A)

sched.process()
