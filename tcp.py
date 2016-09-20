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

scenario=7


# duplex2('node1',ratelimit=1000,MaxSize=100)

if scenario == 0:
  sw=duplex('node1')
  connect('con1',tcpxmit.B,sw.A)
  connect('con2',sw.B,tcprecv.A)
elif scenario == 1:
  link=datalink('link',latency=20)
  connect('con1',tcpxmit.B,link.A)
  connect('con2',link.B,tcprecv.A)
elif scenario == 2:
  sw=eth_switch('sw')
  connect('con1',tcpxmit.B,sw.A)
  connect('con2',sw.B,tcprecv.A)
elif scenario == 3:
  rtr=router('rtr')
  connect('con1',tcpxmit.B,rtr.A)
  connect('con2',rtr.B,tcprecv.A)
elif scenario == 4:
  sw1=vswitch('sw1')
  sw2=vswitch('sw2')
  connect('con3',tcpxmit.B,sw1.A)
  connect('con3',sw1.B,sw2.A)
  connect('con4',sw2.B,tcprecv.A)
elif scenario == 5:
  sw1=vswitch('sw1',"","MPLS()")
  sw2=vswitch('sw2',"MPLS()","")
  connect('con3',tcpxmit.B,sw1.A)
  connect('con3',sw1.B,sw2.A)
  connect('con4',sw2.B,tcprecv.A)
elif scenario == 6:
  sw1=vswitch('sw1',"","MPLS()")
  sw2=vswitch('sw2',"MPLS()","")
  link=datalink('link1',latency=5,trace=True)
  connect('con3',tcpxmit.B,sw1.A)
  connect('con3',sw1.B,link.A)
  connect('con3',link.B,sw2.A)
  connect('con4',sw2.B,tcprecv.A)
elif scenario == 7:
  sw1=vswitch('sw1',"","Dot1Q(vlan=3)")
  sw2=vswitch('sw2',"Dot1Q(vlan=3)","MPLS(label=101)")
  sw3=vswitch('sw3',"MPLS(label=101)","")
  link1=datalink('link1',latency=10,trace=True)
  link2=datalink('link2',latency=50,trace=True)
  connect('con3',tcpxmit.B,sw1.A)
  connect('con3',sw1.B,link1.A)
  connect('con3',link1.B,sw2.A)
  connect('con3',sw2.B,link2.A)
  connect('con3',link2.B,sw3.A)
  connect('con4',sw3.B,tcprecv.A)
elif scenario == 8: # classic architecture
  pon=datalink('pon',latency=10)
  onu=vswitch('onu',"","Dot1Q()")
  olt=vswitch('olt',"Dot1Q()","")
  cpe=vswitch('cpe',"","Dot1Q()")
  bras=vswitch('bras',"Dot1Q()","")
  homerouter=router('hr')
  metrorouter=vswitch('mr',"","MPLS()")
  corerouter=vswitch('cr',"MPLS()","")
  connect('c1',homerouter.B,cpe.A)
  connect('c2',cpe.B,onu.A)
  connect('c3',onu.B,pon.A)
  connect('c4',pon.B,olt.A)
  connect('c5',olt.B,bras.A)
  connect('c6',bras.B,metrorouter.A)
  connect('c7',metrorouter.B,corerouter.A)
  connect('c8',tcpxmit.B,homerouter.A)
  connect('c9',tcprecv.A,corerouter.B)
elif scenario == 9: # 
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
  connect('c8',tcpxmit.B,cpe.A)
  connect('c9',tcprecv.A,coreswitch.B)


sched.process()

