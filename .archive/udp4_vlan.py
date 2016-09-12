from network import *

sched=scheduler(tick=0.001,finish=10)

host1=host('host1',stack='udp')
host2=host('host2',stack='udp')

# sw1=mplsswitch('sw1')
#sw1=eth_switch('sw')
# sw1=router('router')

#sw1=mpls_switch('mpls',labelB=456)
#sw2=mpls_switch('mpls',labelA=456)

sw1=vlan_switch('vlan1',vlanB=1)
sw2=vlan_switch('vlan2',vlanA=1)

link=transmission('link1',latency=10,trace=True)

traf=trafgen('traf',speed=10)
term2=terminal('term2')

connect('con1',traf.B,host1.B)
connect('con2',term2.A,host2.B)
connect('con3',host1.A,sw1.A)
connect('con4',sw1.B,link.A)
connect('con5',link.B,sw2.A)
connect('con6',host2.A,sw2.B)

sched.process()
