from tcp_listener import TCPListener
from tcp_protocol import TCPSocket
from queue import *
from scapy.all import *
from network import *

class duplex2(duplex):
   def __init__(self, *args, **kwargs):
      super(duplex2, self).__init__(*args, **kwargs)
      self.pcapw=PcapWriter(self.name+'.pcap')

   def inspectA(self,stream,name):
      frame=Ether(stream.decode("HEX"))
      frame.time=float(self.nw())
      self.pcapw.write(frame)
      return stream

   def inspectB(self,stream,name):
      frame=Ether(stream.decode("HEX"))
      frame.time=float(self.nw())
      self.pcapw.write(frame)
      return stream

   def __del__(self):
      print "Total packets : %s %d" % (self.name, self.pcount)

class tcpgen(duplex2):
   def __init__(self, *args, **kwargs):
      super(tcpgen, self).__init__(*args, **kwargs)
      self.listener = TCPListener(self.A.get,self.A.put,'1.1.1.1')
      self.conn=TCPSocket(self.listener)
      self.conn.connect('2.2.2.2',80)
      self.worker1()

   @threaded
   def worker1(self):
      for i in range(1,5000):
         stime=self.waittick()
         self.conn.send("A"*250)
      self.waitfor(9000)
      print "closing"
      self.conn.close()
               

class tcpterm(duplex2):
   def __init__(self, *args, **kwargs):
      super(tcpterm, self).__init__(*args, **kwargs)
      self.listener = TCPListener(self.B.get,self.B.put,'2.2.2.2')
      self.conn=TCPSocket(self.listener)
      self.conn.bind('2.2.2.2',80)
      self.worker()

   @threaded
   def worker(self):
      while True:
         data=self.conn.recv(10000,timeout=1)
      self.conn.close()

print conf.netcache.arp_cache

sched=scheduler(tick=0.001,finish=10)

# node1=duplex2('node1',ratelimit=1000,MaxSize=100)

tcpxmit=tcpgen('tcpxmit',stop=3.0)

tcprecv=tcpterm('tcprecv')

#sw=eth_switch('sw')
sw1=vswitch('sw1',"","MPLS()")
sw2=vswitch('sw2',"MPLS()","")
#sw3=vswitch('sw3',"MPLS()","")

link=transmission('link1',latency=5,trace=True)

# traf=trafgen('traf',speed=1)
# term2=terminal('term2')

connect('con3',tcpxmit.B,sw1.A)
connect('con3',sw1.B,sw2.A)
connect('con4',sw2.B,tcprecv.A)

# connect('con3',tcpxmit.B,sw1.A)
# connect('con4',sw1.B,sw2.A)
# connect('lcon1',sw2.B,link.A)
# connect('lcon2',link.B,sw3.A)
# connect('con6',tcprecv.A,sw2.B)

sched.process()

