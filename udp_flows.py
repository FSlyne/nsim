from scapy.all import *
from network import *

sched=scheduler(tick=0.001,finish=10)

host1=host('host1',stack='udp') # Good traffic generator
host2=host('host2',stack='udp',mdrop='00:00:00:00:00:00') # terminal, dropping fake traffic
host3=host('host3',stack='udp',mdst='00:00:00:00:00:00') # fake traffic generator


#host1=host('host1',stack='udp')
#host2=host('host2',stack='udp')

traf=trafgen('traf1',ms1=1)
# traf=trafgen('traf1')
term2=terminal('term2')
flowgen=flowgen('flowgen',start=0.002,stop=2.5,ival=0.300,flowcount=5)

scenario=3

if scenario == 0:
   sw=datalink('node1',capacity=1,MaxSize=10000)
   # sw=datalink('node1',latency=40)
   connect('hostcon1',host1.B,traf.B)
   connect('con1',host1.A,sw.B)
   connect('con2',sw.A,host2.A)
   connect('hostcon2',host2.B,term2.A)
   connect('flow',flowgen.B, host3.B)
   connect('con3',host3.A, sw.B)
elif scenario == 1: # classic architecture
  pon=datalink('pon',latency=10)
  onu=vswitch('onu',"","Dot1Q()")
  olt=vswitch('olt',"Dot1Q()","")
  cpe=vswitch('cpe',"","Dot1Q()")
  bras=vswitch('bras',"Dot1Q()","")
  homerouter=eth_switch('hr')
  metrorouter=vswitch('mr',"","MPLS()")
  corerouter=vswitch('cr',"MPLS()","")
  connect('hostcon1',host1.B,traf.B)
  connect('hostcon2',host2.B,term2.A)
  connect('c1',homerouter.B,cpe.A)
  connect('c2',cpe.B,onu.A)
  connect('c3',onu.B,pon.A)
  connect('c4',pon.B,olt.A)
  connect('c5',olt.B,bras.A)
  connect('c6',bras.B,metrorouter.A)
  connect('c7',metrorouter.B,corerouter.A)
  connect('c8',host2.A,homerouter.A)
  connect('c9',host1.A,corerouter.B)
  #
  connect('flow',flowgen.B, host3.B)
  connect('con3',host3.A, corerouter.B)
elif scenario == 2:
  pon=datalink('pon',latency=10)
  link1=datalink('link1',latency=2)
  link2=datalink('link2',latency=2)
  link3=datalink('link2',latency=2)
  onu=vswitch('onu',"","Dot1Q()")
  olt=vswitch('olt',"Dot1Q()","")
  cpe=vswitch('cpe',"","Dot1Q()")
  bras=vswitch('bras',"Dot1Q()","")
  homerouter=eth_switch('hr')
  metrorouter=vswitch('mr',"","MPLS()")
  corerouter=vswitch('cr',"MPLS()","")
  connect('hostcon1',host1.B,traf.B)
  connect('hostcon2',host2.B,term2.A)
  connect('c1',homerouter.B,cpe.A)
  connect('c2',cpe.B,onu.A)
  connect('c3',onu.B,pon.A)
  connect('c4',pon.B,olt.A)
  connect('c5',olt.B,bras.A)
  connect('c6',bras.B,link1.A)
  connect('c7',link1.B,metrorouter.A)
  connect('c8',metrorouter.B,link2.A)
  connect('c9',link2.B,corerouter.A)
  connect('c10',corerouter.B,link3.A)
  connect('c8',host2.A,homerouter.A)
  connect('c9',host1.A,link3.B)
  #
  connect('flow',flowgen.B, host3.B)
  connect('con3',host3.A, corerouter.B)
elif scenario == 3: # New Arch
  pon=datalink('pon',latency=10)
  onu=vswitch('onu',"","Dot1Q()")
  olt=vswitch('olt',"Dot1Q()","")
  cpe=eth_switch('cpe')
  accessswitch=eth_switch('as')
  metroswitch=eth_switch('ms')
  coreswitch=eth_switch('cs')
  connect('c1',cpe.B,onu.A)
  connect('c2',onu.B,pon.A)
  connect('c3',pon.B,olt.A)
  connect('c4',olt.B,accessswitch.A)
  connect('c5',accessswitch.B,metroswitch.A)
  connect('c6',metroswitch.B,coreswitch.A)
  connect('c8',host1.A,coreswitch.B)
  connect('c9',host2.A,cpe.A)
  connect('hostcon1',host1.B,traf.B)
  connect('hostcon2',host2.B,term2.A)
  #
  connect('flow',flowgen.B, host3.B)
  connect('con3',host3.A, coreswitch.B)
elif scenario == 4: # New Arch
  pon=datalink('pon',latency=2)
  link1=datalink('link1',latency=2)
  link2=datalink('link2',latency=2)
  link3=datalink('link3',latency=2)
  onu=vswitch('onu',"","Dot1Q()")
  olt=vswitch('olt',"Dot1Q()","")
  cpe=eth_switch('cpe')
  accessswitch=eth_switch('as')
  metroswitch=eth_switch('ms')
  coreswitch=eth_switch('cs')
  connect('c1',cpe.B,onu.A)
  connect('c1',onu.B,pon.A)
  connect('c3',pon.B,olt.A)
  connect('c3',olt.B,link1.A)
  connect('c4',link1.B,accessswitch.A)
  connect('c5',accessswitch.B,link2.A)
  connect('c6',link2.B,metroswitch.A)
  connect('c7',metroswitch.B,link3.A)
  connect('c8',link3.B,coreswitch.A)
  connect('c8',host1.A,coreswitch.B)
  connect('c9',host2.A,cpe.A)
  connect('hostcon1',host1.B,traf.B)
  connect('hostcon2',host2.B,term2.A)
  #
  connect('flow',flowgen.B, host3.B)
  halfconnect('con3',host3.A, coreswitch.B)




sched.process()

