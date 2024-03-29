from queue import *
from scapy.all import *

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

class transmission(duplex2):
   def __init__(self, *args, **kwargs):
      super(transmission, self).__init__(*args, **kwargs)
      self.pcapw=PcapWriter(self.name+'.pcap')

   def inspectA(self,stream,name):
#      self.waitfor(0.050)
      stream=super(transmission,self).inspectA(stream,name)
      return stream

   def inspectB(self,stream,name):
#      self.waitfor(0.050)
      stream=super(transmission,self).inspectB(stream,name)
      return stream

class udpgen(duplex2):
   def __init__(self, *args, **kwargs):
      super(udpgen, self).__init__(*args, **kwargs)
      self.worker1()
      self.worker2()

   

   @threaded
   def worker1(self):
      pcount=0
      while True:
         stime=self.waittick()
         if self.stop > 0:
            if float(stime) > float(self.stop):
               time.sleep(0.1)
               break
         timlock,now=self.lock()
         pcount+=1
         payload="%d:%s" % (pcount,stime)
         frame=Ether()/IP()/UDP()/payload
         stream=str(frame).encode("HEX")
         self.A.put(stream)
         self.logwrite("%s Sending %s" % (self.name,payload))
         self.unlock(timlock)

   @threaded
   def worker2(self):
      while True:
         item=self.A.get()
         timlock,now=self.lock()
         eth=Ether(item.decode("HEX"))
         ip=eth[IP]
         udp=ip[UDP]
         self.logwrite("%s Receiving %s" % (self.name,udp.payload))
         self.unlock(timlock)

class udpterm(duplex2):
   def __init__(self, *args, **kwargs):
      super(udpterm, self).__init__(*args, **kwargs)
      self.worker()

   @threaded
   def worker(self):
      while True:
         stream=self.B.get()
         timlock,now=self.lock()
         eth=Ether(stream.decode("HEX"))
         ip=eth[IP]
         udp=ip[UDP]
         item=stream
         self.B.put(item)
         self.unlock(timlock)

sched=scheduler(tick=0.001,finish=500)

node1=transmission('node1',MaxSize=1)
# node1=duplex2('node1')

# udpxmit=udpgen('udpxmit',stop=3.0,MaxSize=500)
udpxmit=udpgen('udpxmt',stop=3.0)

udprecv=udpterm('udprecv')

# hub=xhub('hub',[udpxmit.B,udpxmit1.B,node1.A])

connect('con1',udpxmit.B,node1.A)
connect('con2',udprecv.A,node1.B)

sched.process()

