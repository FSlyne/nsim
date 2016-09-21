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
      payload="A"*20
      for count in range(1,90000):
         now = stime=self.waittick()
#         timlock,now=self.lock()
         load='%d:%s:%s'%(count,now,payload)
         loadbits=len(load)*8
         self.updatestats('trafbits',loadbits,'bits')
         r.hset("pkt:%07d"%count ,"sendtime",now)
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

sched=scheduler(tick=0.001,finish=10)

tcpxmit=tcpgen('tcpxmit',stop=3.0)
tcprecv=tcpterm('tcprecv')

scenario=0

#host1=host('host1',stack='udp') # Good traffic generator
#host2=host('host2',stack='udp',mdrop='00:00:00:00:00:00') # terminal, dropping fake traffic
host3=host('host3',stack='udp',mdst='11:22:33:44:55:66') # fake traffic generator

#host1=host('host1',stack='udp')
#host2=host('host2',stack='udp')

#traf=trafgen('traf1',ms1=1)
# traf=trafgen('traf1')
#term2=terminal('term2')
flowgen=flowgen('flowgen',start=0.002,stop=2.5,ival=0.300,flowcount=5)

scenario=2

if scenario == 0:
#   sw=datalink('node1',capacity=1,MaxSize=10000)
   sw=datalink('node1',latency=40)
   connect('con1',tcpxmit.B,sw.B)
   connect('con2',sw.A,tcprecv.A)
   connect('flow',flowgen.B, host3.B)
   halfconnect('con3',host3.A, sw.B)
elif scenario == 1: # classic architecture
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
elif scenario == 2: # New Arch
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
  connect('c8',tcpxmit.B,coreswitch.B)
  connect('c9',tcprecv.A,cpe.A)
  #
  connect('flow',flowgen.B, host3.B)
  halfconnect('con3',host3.A, coreswitch.B)



sched.process()

