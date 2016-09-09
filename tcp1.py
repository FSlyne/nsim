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

   def __del__(self):
      print "Total packets : %s %d" % (self.name, self.pcount)

class tcpgen(duplex2):
   def __init__(self, *args, **kwargs):
      super(tcpgen, self).__init__(*args, **kwargs)
      self.worker1()

   @threaded
   def worker1(self):
      pcount=0
      seq=10
      syn=Ether()/IP()/TCP(flags="S", seq=seq)
      stream=str(syn).encode("HEX")
      self.A.put(stream)
      item=self.A.get()
      print item
      eth=Ether(item.decode("HEX"))
      ip=eth[IP]; synack=ip[TCP]
      my_ack=synack.seq+1;seq=seq+1
      ack=Ether()/IP()/TCP(flags="A",seq=seq,ack=my_ack)
      stream=str(ack).encode("HEX")
      self.A.put(stream)

      while True:
         stime=self.waittick()
         if self.stop > 0:
            if float(stime) > float(self.stop):
               time.sleep(0.1)
               continue
         timlock,now=self.lock()
         pcount+=1
         payload="%d:%s" % (pcount,stime)
         seq=seq+1; my_ack=my_ack+len(payload)
         psh=Ether()/IP()/TCP(flags="PA",seq=seq,ack=my_ack)/payload
         stream=str(psh).encode("HEX")
         self.A.put(stream)
         self.logwrite("%s Sending %s" % (self.name,payload))
         self.unlock(timlock)
         

class tcpterm(duplex2):
   def __init__(self, *args, **kwargs):
      super(tcpterm, self).__init__(*args, **kwargs)
      self.worker()

   @threaded
   def worker(self):
      stream=self.B.get()
      timlock,now=self.lock()
      eth=Ether(stream.decode("HEX"))
      ip=eth[IP]
      syn=ip[TCP]
      seq=syn.seq; ack=syn.seq+1
      synack=Ether()/IP()/TCP(flags="SA",seq=seq,ack=ack,options=[('MSS', 1460)])
      stream=str(synack).encode("HEX")
      self.B.put(stream)
      self.unlock(timlock)
      while True:
         stream=self.B.get()
         timlock,now=self.lock()
         eth=Ether(stream.decode("HEX"))
         ip=eth[IP]
         psh=ip[TCP]
         payload=psh.payload
         ack=ack+len(payload)
         seq=syn.seq # ????
         data=Ether()/IP()/TCP(flags="PA",seq=seq,ack=ack, options=[('MSS', 1460)])/payload
         stream=str(data).encode("HEX")
         self.B.put(stream)
         self.unlock(timlock)

sched=scheduler(tick=0.001,finish=10)

# node1=duplex2('node1',ratelimit=1000,MaxSize=100)
node1=duplex2('node1')

tcpxmit=tcpgen('tcpxmit',stop=3.0)

tcprecv=tcpterm('tcprecv')

connect('con1',tcpxmit.B,node1.A)
connect('con2',tcprecv.A,node1.B)

sched.process()

