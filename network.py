from queue import *
from scapy.all import *
from utilities import *

class MPLS(Packet):
   name = "MPLS"
   fields_desc =  [ BitField("label", 3, 20),
                    BitField("cos", 0, 3),
                    BitField("s", 1, 1),
                    ByteField("ttl", 0)  ]


bind_layers(Ether, MPLS, type = 0x8847) # Marks MPLS
bind_layers(MPLS, MPLS, bottom_of_label_stack = 0) # We're not at the bottom yet
bind_layers(MPLS, IP)

class dataconnect(connect):
   def __init__(self, *args, **kwargs):
      kwargs['ratio'] = 2 # 2 chars in queue eqiv. 1 byte of application data
      super(dataconnect, self).__init__(*args, **kwargs)

class datalink(duplex):
   def __init__(self, *args, **kwargs):
      self.name=args[0]
      self.capacity = kwargs.get('capacity',0) # Mbps
      self.trace = kwargs.get('trace',False) # turn on/off pcap tracing
      self.ber = kwargs.get('ber',0) # 10^ber, ber negative
      self.profile = kwargs.get('profile',False) # profile frames
      if 'capacity' in kwargs:
         del kwargs['capacity']
      if 'trace' in kwargs:
         del kwargs['trace']
      if 'ber' in kwargs:
         del kwargs['ber']
      if 'profile' in kwargs:
         del kwargs['profile']
      if self.trace:
         self.pcapw=PcapWriter(self.name+'.pcap')
      if self.capacity >0:
         kwargs['ratelimit'] = 1000000*self.capacity
   
      kwargs['ratio'] = 2 # 2 chars in queue eqiv. 1 byte of application data
      super(datalink, self).__init__(*args, **kwargs)

   def inspectA(self,stream,name):
      timlock,now=self.lock()
      drop=False
      frame=Ether(stream.decode("HEX"))
      if self.profile:
         self.prof(frame)
      if not self.ber == 0:
         bits=len(frame)*8
         if packet_drop(bits,self.ber):
            drop=True
            self.updatestats(self.name,1,'pktdrp')
      if drop:
         stream=""
      elif self.trace:
         frame.time=float(self.nw())
         self.pcapw.write(frame)
      self.unlock(timlock)
      return stream

   def inspectB(self,stream,name):
      timlock,now=self.lock()
      drop=False
      frame=Ether(stream.decode("HEX"))
      if self.profile:
         self.prof(frame)
      if not self.ber == 0:
         bits=len(frame)*8
         if packet_drop(bits,self.ber):
            drop=True
            self.updatestats(self.name,1,'pktdrp')
      if drop:
         stream="" 
      elif self.trace:
         frame.time=float(self.nw())
         self.pcapw.write(frame)
      self.unlock(timlock)
      return stream

   def prof(self,frame):
      counter = 0
      while True:
         layer=frame.getlayer(counter)
         if (layer != None):
            try:
               v=int(self.r.hget("nodestat:%s" % self.name,layer.name))
            except:
               v=0
            v+=len(layer)
            self.r.hset("nodestat:%s"%self.name,layer.name,v)
         else:
            break
         counter += 1



class eth_switch(object):
   def __init__(self,name,profile=False):
      self.name=name
      self.profile=profile
      self.up=self.eth_up(name+':up',profile=profile)
      self.down=self.eth_down(name+':down',profile=profile)
      self.A=self.up.A
      self.B=self.down.B

      connect('cap',self.up.B,self.down.A)

   class eth_up(duplex):
       def __init__(self, *args, **kwargs):
          self.profile = kwargs.get('profile',False) # profile frames
          if 'profile' in kwargs:
             del kwargs['profile']
          super(eth_switch.eth_up, self).__init__(*args, **kwargs)

       def inspectA(self,stream,name):
          if self.profile:
             self.r.hincrby("nodestat:%s"%self.name,'eth_fwd',1)
          return stream

       def inspectB(self,stream,name):
          return stream


   class eth_down(duplex):
       def __init__(self, *args, **kwargs):
          self.profile = kwargs.get('profile',False) # profile frames
          if 'profile' in kwargs:
             del kwargs['profile']
          super(eth_switch.eth_down, self).__init__(*args, **kwargs)

       def inspectA(self,stream,name):
          if self.profile:
             self.r.hincrby("nodestat:%s"%self.name,'eth_fwd',1)
          return stream

       def inspectB(self,stream,name):
          return stream

class router(object):
   def __init__(self,name,profile=False):
      self.name=name
      self.profile=profile
      self.up=self.route_up(name+':up',profile=profile)
      self.down=self.route_down(name+':down',profile=profile)
      self.A=self.up.A
      self.B=self.down.B

      connect('cap',self.up.B,self.down.A)

   class route_up(duplex):
       def __init__(self, *args, **kwargs):
          self.profile = kwargs.get('profile',False) # profile frames
          if 'profile' in kwargs:
             del kwargs['profile']
          super(router.route_up, self).__init__(*args, **kwargs)

       def inspectA(self,stream,name):
          if self.profile:
             self.r.hincrby("nodestat:%s"%self.name,'ip_route',1)
          stream1=stream.decode("HEX")
          stream1=Ether(stream1)
          p=manip(stream1)
          p.swaplayer(0,"Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')")
          p.build
          stream=str(p.pkt).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream1=stream.decode("HEX")
          stream1=Ether(stream1)
          p=manip(stream1)
          p.swaplayer(0,"Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')")
          p.build()
          stream=str(p.pkt).encode("HEX")
          return stream

   class route_down(duplex):
       def __init__(self, *args, **kwargs):
          self.profile = kwargs.get('profile',False) # profile frames
          if 'profile' in kwargs:
             del kwargs['profile']
          super(router.route_down, self).__init__(*args, **kwargs)

       def inspectA(self,stream,name):
          if self.profile:
             self.r.hincrby("nodestat:%s"%self.name,'ip_route',1)
          stream1=stream.decode("HEX")
          stream1=Ether(stream1)
          p=manip(stream1)
          p.swaplayer(0,"Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')")
          p.build()
          stream=str(p.pkt).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream1=stream.decode("HEX")
          stream1=Ether(stream1)
          p=manip(stream1)
          p.swaplayer(0,"Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')")
          p.build()
          stream=str(p.pkt).encode("HEX")
          return stream
         
class vswitch(object):
   def __init__(self,name,tagA="",tagB="",debug=False,profile=False):
      self.name=name
      self.profile=profile
      self.up=self.vswitch_up(name+':up',tagA=tagA,tagB=tagB,debug=debug,profile=profile)
      self.down=self.vswitch_down(name+':down',tagA=tagA,tagB=tagB,debug=debug,profile=profile)
      self.A=self.up.A
      self.B=self.down.B
      self.debug=debug


      connect('cap',self.up.B,self.down.A)

   class vswitch_up(duplex):
       def __init__(self,*args, **kwargs):
          self.tagA = kwargs.get('tagA')
          self.tagB = kwargs.get('tagB')
          self.profile = kwargs.get('profile',False) # profile frames
          if 'profile' in kwargs:
             del kwargs['profile']
          if 'tagA' in kwargs:
             del kwargs['tagA']
          if 'tagB' in kwargs:
             del kwargs['tagB']
          super(vswitch.vswitch_up, self).__init__(*args, **kwargs)

       def inspectA(self,stream,name):
          stream1=stream.decode("HEX")
          stream1=Ether(stream1)
          p=manip(stream1,self.name)
          if self.debug:
            print "inspectA1a",name,p.struct,"\n"
          p.settun(self.tagA,self.tagB)
          p.build()
          if self.debug:
            print "inspectA1b",name,p.struct,"\n",p.line,"\n"
          stream=str(p.pkt).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream1=stream.decode("HEX")
          stream1=Ether(stream1)
          p=manip(stream1,self.name)
          if self.debug:
            print "inspectB1a",name,p.struct,"\n"
          p.settun(self.tagB,self.tagA)
          p.build()
          if self.debug:
            print "inspectB1b",name,p.struct,"\n"
          stream=str(p.pkt).encode("HEX")
          return stream

   class vswitch_down(duplex):
       def __init__(self,*args, **kwargs):
          self.tagA = kwargs.get('tagA')
          self.tagB = kwargs.get('tagB')
          self.profile = kwargs.get('profile',False) # profile frames
          if 'profile' in kwargs:
             del kwargs['profile']
          if 'tagA' in kwargs:
             del kwargs['tagA']
          if 'tagB' in kwargs:
             del kwargs['tagB']
          super(vswitch.vswitch_down, self).__init__(*args, **kwargs)

       def inspectA(self,stream,name):
          stream1=stream.decode("HEX")
          stream1=Ether(stream1)
          p=manip(stream1,self.name)
          if self.debug:
            print "inspectA2a",name,p.struct,"\n"
          p.settun(self.tagB,self.tagA)
          p.build
          if self.debug:
            print "inspectA2b",name,p.struct,"\n"
          stream=str(p.pkt).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream1=stream.decode("HEX")
          stream1=Ether(stream1)
          p=manip(stream1,self.name)
          if self.debug:
             print "inspectB2a",name,p.struct
          p.settun(self.tagA,self.tagB)
          p.build
          if self.debug:
            print "inspectB2b",name,p.struct
          stream=str(p.pkt).encode("HEX")
          return stream

class host(object):
   def __init__(self,name,stack='udp',
        mdrop='',
        msrc='00:00:00:00:00:11',
        mdst='00:00:00:00:00:11',
        isrc='1.1.1.1',
        idst='2.2.2.2',
        dport=2345):
      sport=random.randint(1024,64000)
      self.name=name
      self.up=self.eth_up(name+':up',mdrop=mdrop,
            msrc=msrc,mdst=mdst,isrc=isrc,
            idst=idst,sport=sport,dport=dport)
      self.A=self.up.A
      self.B=self.up.B

   class eth_up(duplex):
       def __init__(self, *args, **kwargs):
          self.mdrop = kwargs.get('mdrop','')
          if 'mdrop' in kwargs:
             del kwargs['mdrop']
          self.msrc = kwargs.get('msrc','00:00:00:00:00:11')
          if 'msrc' in kwargs:
             del kwargs['msrc']
          self.mdst = kwargs.get('mdst','00:00:00:00:00:11')
          if 'mdst' in kwargs:
             del kwargs['mdst']
          self.isrc = kwargs.get('isrc','1.1.1.1')
          if 'isrc' in kwargs:
             del kwargs['isrc']
          self.idst = kwargs.get('idst','2.2.2.2')
          if 'idst' in kwargs:
             del kwargs['idst']
          self.sport = kwargs.get('sport',8888)
          if 'sport' in kwargs:
             del kwargs['sport']
          self.dport = kwargs.get('dport',2345)
          if 'dport' in kwargs:
             del kwargs['dport']
          super(host.eth_up, self).__init__(*args, **kwargs)

       def inspectA(self,stream,name):
          eth=Ether(stream.decode("HEX"))
          if self.mdrop:
             if eth.dst == self.mdrop:
                return ''
          try:
            ip=eth[IP]
            udp=ip[UDP]
          except:
            return "Host Error"
#          stream=str(payload).encode("HEX")
          return udp.payload

       def inspectB(self,payload,name):
#          print "payload B:",payload
#          stream=payload.decode("HEX")
          frame=Ether(src=self.msrc,dst=self.mdst)/IP(src=self.isrc,dst=self.idst)/UDP(sport=self.sport,dport=self.dport)/payload
          stream=str(frame).encode("HEX")
          return stream

class manip(object):
   def __init__(self,pkt,name='null'):
      self.pkt=pkt
      self.name=name
      self.tunlist=['PPP','PPPoE','MPLS','Dot1Q','Ether']
      self.valid_protos=["Ether","IP","MPLS","Dot1Q","PPPoE","UDP","TCP"]
      self.attributes=["src","dst","sport","dport","flags","window","seq","ack","dataofs"]
      self.align()
      
   def align(self):
      self.pkt.hide_defaults()
      self.cmd =self.pkt.command()
      self.struct = self.cmd.split("/")
      self.line="/".join(self.struct)
      self.shortstruct=list(self.struct)
      del self.shortstruct[-1]
      self.shortline="/".join(self.shortstruct)

   def getlayers(self):
      layers = []
      counter = 0
      while True:
         layer = self.pkt.getlayer(counter)
         if (layer != None):
            layers.append(layer.name)
         else:
            break
         counter += 1
      return layers

   def parse_okay(self):
      if 'IP' in self.getlayers():
         return True
      else:
         return False

   def display(self):
      print self.struct
   def numlayers(self):
      return len(self.struct)

   def show(self):
      self.build()
      self.pkt.show()

   def split(self,n):
      return self.struct[0:n],self.struct[n+1:]

   def find_hitun(self):
      a=self.numlayers()-1
      for n in self.struct[::-1]:
         for m in self.tunlist:
            if m in n:
               return n,m,a
         a=a-1
      return "","",a


   def addlayer(self,n,layer):
      self.struct.insert(n,layer)

   def dellayer(self,n):
      del self.struct[n]

   def swaplayer(self,n,layer):
     # n starts at 0
      self.struct[n] = layer
      
   def clean(self):
      for i,n in enumerate(self.struct):
         try:
            proto,field=n.replace("(","|").replace(")","|").split("|")[0:2]
         except:
            print i,n
            proto,field="",""
         if proto in self.valid_protos:
            p=[]
            for l in field.split(","):
               for m in self.attributes:
                  if m in l:
                     p.append(l)
            newfield = ",".join(p)
         else:
            newfield=field
         self.struct[i]=proto+"("+newfield+")"
            

   def build(self):
      self.pkt.hide_defaults()
      self.clean()
      structline="/".join(self.struct)
      try:
         pkt=eval(structline)
      except:
         pkt=self.pkt
         print "Packet Build exception:",structline
         print self.struct
      self.pkt=pkt
      self.align()

   def addtun(self,tunlayer):
      n,m,a=self.find_hitun()
      self.addlayer(a+1,tunlayer)

   def deltun(self):
      n,m,a=self.find_hitun()
      if a <= 0:
         return
      self.dellayer(a)

   def swaptun(self,tun2):
      self.deltun()
      self.addtun(tun2)

   def hexdump(self):
      self.build()
      return self.pkt.hexdump()

   def settun(self, tagA, tagB):
      if tagB:
         if  tagA:
            r.hincrby("nodestat:%s"%self.name,'label_swap',1)
            self.swaptun(tagB)
         else:
            r.hincrby("nodestat:%s"%self.name,'label_push',1)
            self.addtun(tagB)
      else:
         if tagA:
            r.hincrby("nodestat:%s"%self.name,'label_pop',1)
            self.deltun()
         else:
            r.hincrby("nodestat:%s"%self.name,'label_null')
            pass


