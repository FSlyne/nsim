from tcp_listener import TCPListener
from tcp_protocol import TCPSocket
from queue import *
from scapy.all import *
from network import *


class tcpgen(datalink):
   def __init__(self, *args, **kwargs):
      super(tcpgen, self).__init__(*args, **kwargs)
      self.listener = TCPListener(self.A.get,self.A.put,'1.1.1.1')
      self.conn=TCPSocket(self.listener)
      self.conn.connect('2.2.2.2',80)
      self.worker1()

   @threaded
   def worker1(self):
      payload="A"*200
      for count in range(1,5000):
         now = stime=self.waittick()
#         timlock,now=self.lock()
         load='%d:%s:%s'%(count,now,payload)
         loadbits=len(load)*8
         self.updatestats('trafbits',loadbits,'bits')
         r.hset("pkt:%07d"%count ,"sendtime","%s:%d" %(now,len(payload)))
         self.conn.send(load)
#         self.unlock(timlock)
      self.waitfor(1000)
      print "closing"
      self.conn.close()


class tcpterm(datalink):
   def __init__(self, *args, **kwargs):
      super(tcpterm, self).__init__(*args, **kwargs)
      self.listener = TCPListener(self.B.get,self.B.put,'2.2.2.2')
      self.conn=TCPSocket(self.listener)
      self.conn.bind('2.2.2.2',80)
      self.worker()

   @threaded
   def worker(self):
      while True:
         item=str(self.conn.recv(10000,timeout=1))
#         print item
         timlock,now=self.lock()
         count,sendnow,payload=item.split(':')
         r.hset("pkt:%07d"%int(count),"recvtime",now)
         self.unlock(timlock)
      self.conn.close()

print conf.netcache.arp_cache

sched=scheduler(tick=0.001,finish=5)

tcpxmit=tcpgen('tcpxmit',stop=3.0)
tcprecv=tcpterm('tcprecv')


host1=host('host1',stack='udp') # Good traffic generator
host2=host('host2',stack='udp',mdrop='00:00:00:00:00:00') # terminal, dropping fake traffic
host3=host('host3',stack='udp',mdst='11:22:33:44:55:66') # fake traffic generator

smallbuffers=8000
standardbuffers=64000


traf=trafgen('traf1',ms1=1)
# traf=trafgen('traf1')
#term2=terminal('term2')

scenario=6

if scenario == 0:
#   flowgen=flowgen('flowgen',start=0.002,stop=2.5,ival=0.300,flowcount=5)
#   sw=datalink('node1',capacity=1,MaxSize=10000)
   sw=datalink('node1',latency=10)
   connect('con1',tcpxmit.B,sw.B)
   connect('con2',sw.A,tcprecv.A)
#   connect('flow',flowgen.B, host3.B)
#   halfconnect('con3',host3.A, sw.B)
elif scenario == 1: # classic architecture
  flowgen=flowgen('flowgen',start=0.002,stop=1.0,ival=0.05,flowcount=5)
  pon=datalink('pon',latency=10)
  onu=vswitch('onu',"","Dot1Q()")
  olt=vswitch('olt',"Dot1Q()","")
  cpe=vswitch('cpe',"","Dot1Q()")
  bras=vswitch('bras',"Dot1Q()","")
  homerouter=eth_switch('hr')
  metrorouter=vswitch('mr',"","MPLS()")
  corerouter=vswitch('cr',"MPLS()","")
  connect('c1',homerouter.B,cpe.A)
  connect('c2',cpe.B,onu.A)
  connect('c3',onu.B,pon.A)
  connect('c4',pon.B,olt.A)
  connect('c5',olt.B,bras.A)
  connect('c6',bras.B,metrorouter.A)
  connect('c7',metrorouter.B,corerouter.A)
  connect('c8',tcprecv.A,homerouter.A)
  connect('c9',tcpxmit.B,corerouter.B)
  #
  connect('flow',flowgen.B, host3.B)
  halfconnect('con3',host3.A, corerouter.B)
elif scenario == 2: # classic architecture - standard buffers
  flowgen=flowgen('flowgen',start=0.002,stop=1.0,ival=0.05,flowcount=5)
  pon=datalink('pon',latency=2,capacity=10,ber=-12,MaxSize=standardbuffers)
  link1=datalink('link1',latency=2,ber=-12,MaxSize=standardbuffers)
  link2=datalink('link2',latency=2,ber=-12,capacity=5,MaxSize=standardbuffers)
  link3=datalink('link3',latency=2,ber=-12,MaxSize=standardbuffers)
  onu=vswitch('onu',"","Dot1Q(vlan=22)",MaxSize=standardbuffers)
  olt=vswitch('olt',"Dot1Q(vlan=22)","",MaxSize=standardbuffers)
  cpe=vswitch('cpe',"","Dot1Q(vlan=35)",MaxSize=standardbuffers)
  bras=vswitch('bras',"Dot1Q(vlan=35)","",MaxSize=standardbuffers)
  homerouter=eth_switch('hr',MaxSize=standardbuffers)
  metrorouter=vswitch('mr',"","MPLS(label=250)",MaxSize=standardbuffers)
  corerouter=vswitch('cr',"MPLS(label=250)","",MaxSize=standardbuffers)
  connect('hostcon1',host1.B,traf.B)
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
  connect('c11',tcprecv.A,homerouter.A)
  connect('c12',tcpxmit.B,link3.B)
  #
  connect('flow',flowgen.B, host3.B)
  halfconnect('con3',host3.A, corerouter.B)
elif scenario == 3: # classic architecture - standard buffers, Aged Queue (to deal with buffer bloat)
  flowgen=flowgen('flowgen',start=0.002,stop=1.0,ival=0.05,flowcount=5)
  pon=datalink('pon',latency=2,capacity=10,ber=-12,MaxSize=standardbuffers)
  link1=datalink('link1',latency=2,ber=-12,MaxSize=standardbuffers)
  link2=datalink('link2',latency=2,ber=-12,capacity=5,MaxSize=standardbuffers)
  link3=datalink('link3',latency=2,ber=-12,MaxSize=standardbuffers)
  onu=vswitch('onu',"","Dot1Q(vlan=22)",MaxSize=standardbuffers)
  olt=vswitch('olt',"Dot1Q(vlan=22)","",MaxSize=standardbuffers)
  cpe=vswitch('cpe',"","Dot1Q(vlan=35)",MaxSize=standardbuffers)
  bras=vswitch('bras',"Dot1Q(vlan=35)","",MaxSize=standardbuffers)
  homerouter=eth_switch('hr',MaxSize=standardbuffers)
  metrorouter=vswitch('mr',"","MPLS(label=250)",MaxSize=standardbuffers,age=10)
  corerouter=vswitch('cr',"MPLS(label=250)","",MaxSize=standardbuffers,age=10)
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
  connect('c11',tcprecv.A,homerouter.A)
  connect('c12',tcpxmit.B,link3.B)
  #
  connect('flow',flowgen.B, host3.B)
  halfconnect('con3',host3.A, corerouter.B)
elif scenario == 4: # New Arch - standard buffers
  flowgen=flowgen('flowgen',start=0.002,stop=1.0,ival=0.05,flowcount=5)
  pon=datalink('pon',latency=2,ber=-12,capacity=10,MaxSize=standardbuffers)
  link1=datalink('link1',latency=2,ber=-12,MaxSize=standardbuffers)
  link2=datalink('link2',latency=2,ber=-12,MaxSize=standardbuffers)
  link3=datalink('link3',latency=2,ber=-12,MaxSize=standardbuffers,capacity=5)
  onu=vswitch('onu',"","Dot1Q(vlan=70)",MaxSize=standardbuffers)
  olt=vswitch('olt',"Dot1Q(vlan=70)","",MaxSize=standardbuffers)
  cpe=eth_switch('cpe',MaxSize=standardbuffers)
  accessswitch=eth_switch('as',MaxSize=standardbuffers)
  metroswitch=eth_switch('ms',MaxSize=standardbuffers)
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
  connect('c9',tcpxmit.B,coreswitch.B)
  connect('c10',tcprecv.A,cpe.A)
  #
  connect('flow',flowgen.B, host3.B)
  halfconnect('con3',host3.A, coreswitch.B)
elif scenario == 5: # New Arch - smallbuffers
  flowgen=flowgen('flowgen',start=0.002,stop=1.0,ival=0.05,flowcount=5)
  pon=datalink('pon',latency=2,ber=-12,capacity=10,MaxSize=standardbuffers)
  link1=datalink('link1',latency=2,ber=-12,MaxSize=standardbuffers)
  link2=datalink('link2',latency=2,ber=-12,MaxSize=standardbuffers)
  link3=datalink('link3',latency=2,ber=-12,MaxSize=standardbuffers,capacity=5)
  onu=vswitch('onu',"","Dot1Q(vlan=70)",MaxSize=standardbuffers)
  olt=vswitch('olt',"Dot1Q(vlan=70)","",MaxSize=standardbuffers)
  cpe=eth_switch('cpe',MaxSize=standardbuffers)
  accessswitch=eth_switch('as',MaxSize=smallbuffers)
  metroswitch=eth_switch('ms',MaxSize=smallbuffers)
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
  connect('c9',tcpxmit.B,coreswitch.B)
  connect('c10',tcprecv.A,cpe.A)
  #
  connect('flow',flowgen.B, host3.B)
  halfconnect('con3',host3.A, coreswitch.B)
elif scenario == 6: # New Arch - small buffers and flow control
  flowgen=flowgen('flowgen',start=0.002,stop=1.0,ival=0.05,flowcount=5,fblimit=3)
  pon=datalink('pon',latency=2,ber=-12,capacity=10,MaxSize=smallbuffers)
  link1=datalink('link1',latency=2,ber=-12,MaxSize=smallbuffers)
  link2=datalink('link2',latency=2,ber=-12,MaxSize=smallbuffers)
  link3=datalink('link3',latency=2,ber=-12,MaxSize=smallbuffers,capacity=5)
  onu=vswitch('onu',"","Dot1Q(vlan=70)",MaxSize=smallbuffers)
  olt=vswitch('olt',"Dot1Q(vlan=70)","",MaxSize=smallbuffers)
  cpe=eth_switch('cpe',MaxSize=smallbuffers)
  accessswitch=eth_switch('as',MaxSize=smallbuffers)
  metroswitch=eth_switch('ms',MaxSize=smallbuffers)
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
  connect('c9',tcpxmit.B,coreswitch.B)
  connect('c10',tcprecv.A,cpe.A)
  #
  connect('flow',flowgen.B, host3.B)
  halfconnect('con3',host3.A, coreswitch.B)



sched.process()

