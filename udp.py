from scapy.all import *
from network import *

sched=scheduler(tick=0.001,finish=10)


host1=host('host1',stack='udp')
host2=host('host2',stack='udp')

# traf=trafgen('traf1',ms1=1)
traf=trafgen('traf1')
term2=terminal('term2')

scenario=4

# duplex2('node1',ratelimit=1000,MaxSize=100)

if scenario == 0:
  sw=duplex('node1')
  connect('hostcon1',host1.B,traf.B)
  connect('con1',host1.A,sw.A)
  connect('con2',sw.B,host2.A)
  connect('hostcon2',host2.B,term2.A)
elif scenario == 1:
  sw=datalink('node1',ratelimit=1000,MaxSize=1000)
  connect('hostcon1',host1.B,traf.B)
  connect('con1',host1.A,sw.A)
  connect('con2',sw.B,host2.A)
  connect('hostcon2',host2.B,term2.A)
elif scenario == 2:
  link=datalink('link',latency=50,trace=True,debug=True,ber=-9)
#  link=datalink('link',latency=10)
  connect('hostcon1',host1.B,traf.B)
  dataconnect('con1',host1.A,link.A)
  dataconnect('con2',link.B,host2.A)
  connect('hostcon2',host2.B,term2.A)
elif scenario == 3:
  sw=eth_switch('sw',profile=True)
  connect('hostcon1',host1.B,traf.B)
  connect('con1',host1.A,sw.A)
  connect('con2',sw.B,host2.A)
  connect('hostcon2',host2.B,term2.A)
elif scenario == 4:
  rtr=router('rtr',profile=True)
  connect('hostcon1',host1.B,traf.B)
  connect('con1',host1.A,rtr.A)
  connect('con2',rtr.B,host2.A)
  connect('hostcon2',host2.B,term2.A)
elif scenario == 5:
  vsw=vswitch('vsw')
  connect('hostcon1',host1.B,traf.B)
  connect('con1',host1.A,vsw.A)
  connect('con2',vsw.B,host2.A)
  connect('hostcon2',host2.B,term2.A)
elif scenario == 6:
  sw1=vswitch('sw1',"","MPLS()")
  sw2=vswitch('sw2',"MPLS()","")
  connect('hostcon1',host1.B,traf.B)
  connect('con3',host1.A,sw1.A)
  connect('con3',sw1.B,sw2.A)
  connect('con4',sw2.B,host2.A)
  connect('hostcon2',host2.B,term2.A)
elif scenario == 7:
  sw1=vswitch('sw1',"","MPLS()")
  sw2=vswitch('sw2',"MPLS()","")
  link=datalink('link1',latency=100,trace=True)
  connect('hostcon1',host1.B,traf.B)
  connect('con3',host1.A,sw1.A)
  connect('con3',sw1.B,link.A)
  connect('con3',link.B,sw2.A)
  connect('con4',sw2.B,host2.A)
  connect('hostcon2',host2.B,term2.A)

sched.process()

