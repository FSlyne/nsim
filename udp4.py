from network import *

sched=scheduler(tick=0.001,finish=10)

host1=host('host1',stack='udp')
host2=host('host2',stack='udp')

# sw=eth_switch('sw')
# sw=duplex('node')
sw1=vswitch('sw1',"","")
sw2=vswitch('sw2',"MPLS()","Dot1Q()")
sw3=vswitch('sw3',"Dot1Q()","")

# link=transmission('link1',latency=5,trace=True)

traf=trafgen('traf',ms1=1)
term2=terminal('term2')

connect('con1',traf.B,host1.B)
connect('con2',term2.A,host2.B)
connect('con3',sw1.A,host1.A)
connect('con4',sw1.B,sw2.A)
connect('con5',sw2.B,sw3.A)
connect('con4',sw3.B,host2.A)

sched.process()
