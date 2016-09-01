from tcp_listener import TCPListener
from tcp_protocol import TCPSocket
from queue import *
from scapy.all import *

class duplex2(duplex):
   def __init__(self, *args, **kwargs):
      super(duplex2, self).__init__(*args, **kwargs)
      self.pcapw=PcapWriter(self.name+'.pcap')

   def inspect(self,stream,name):
      frame=Ether(stream.decode("HEX"))
      frame.time=float(self.nw())
      self.pcapw.write(frame)
      return stream

   def __del__(self):
      print "Total packets : %s %d" % (self.name, self.pcount)

class tcpgen(duplex2):
   def __init__(self, *args, **kwargs):
      super(tcpgen, self).__init__(*args, **kwargs)
      self.worker1()

   @threaded
   def worker1(self):
      listener = TCPListener(self.A.get,self.A.put,'1.1.1.1')
      conn=TCPSocket(listener)
      conn.connect('2.2.2.2',80)
      for i in range(1,5):
         conn.send("Hello")
         data=conn.recv(10000,timeout=4)
         if data:
           print data
      conn.close()
         

class tcpterm(duplex2):
   def __init__(self, *args, **kwargs):
      super(tcpterm, self).__init__(*args, **kwargs)
      self.worker()

   @threaded
   def worker(self):
      listener = TCPListener(self.B.get,self.B.put,'2.2.2.2')
      conn=TCPSocket(listener)
      conn.bind('2.2.2.2',80)
      while True:
         data=conn.recv(10000,timeout=1)
         conn.send("Goodbye") 
         if data:
            print data
      conn.close()

sched=scheduler(tick=0.01,finish=500)

# node1=duplex2('node1',ratelimit=1000,MaxSize=100)
node1=duplex2('node1')

tcpxmit=tcpgen('tcpxmit',stop=3.0)

tcprecv=tcpterm('tcprecv')

connect('con1',tcpxmit.B,node1.A)
connect('con2',tcprecv.A,node1.B)

sched.process()

