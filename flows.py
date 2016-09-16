from scapy.all import *
from network import *

sched=scheduler(tick=0.001,finish=10)

host1=host('host1',stack='udp')
host2=host('host2',stack='udp',mdrop='00:00:00:00:00:00')
host3=host('host3',stack='udp',mdst='00:00:00:00:00:00')

#traf=trafgen('traf1',ms1=1)
traf=trafgen('traf1')
term2=terminal('term2')
flowgen=flowgen('flowgen',start=0.002,stop=2.5,ival=0.300,flowcount=5)

scenario=3

sw=datalink('node1',capacity=1,MaxSize=10000)
# sw=datalink('node1',latency=40)
connect('hostcon1',host1.B,traf.B)
connect('con1',host1.A,sw.A)
connect('con2',sw.B,host2.A)
connect('hostcon2',host2.B,term2.A)
connect('flow',flowgen.B, host3.B)
connect('con3',host3.A, sw.A)


sched.process()

