from queue import *
from scapy.all import *

class udp_stack(object):
   def __init__(self,name,capped=False,based=False):
      self.layer1=eth_layer('ethernet_layer')
      self.layer2=ip_layer('ip_layer')
      self.layer3=udp_layer('udp_layer')
      self.A=self.layer1.A
      self.B=self.layer1.B
      self.C=self.layer3.C
      self.D=self.layer3.D

      connect('J1',self.layer1.C,self.layer2.A)
      connect('J2',self.layer2.B,self.layer1.D)

      connect('J3',self.layer2.C,self.layer3.A)
      connect('J4',self.layer3.B,self.layer2.D)

      if capped:
         connect('cap',self.layer3.C,self.layer3.D)

      if based:
         connect('cap',self.layer1.B,self.layer1.A)

class ip_stack(object):
   def __init__(self,name,capped=False,based=False):
      self.layer1=eth_layer('ethernet_layer')
      self.layer2=ip_layer('ip_layer')
      self.A=self.layer1.A
      self.B=self.layer1.B
      self.C=self.layer2.C
      self.D=self.layer2.D

      connect('J1',self.layer1.C,self.layer2.A)
      connect('J2',self.layer2.B,self.layer1.D)

      if capped:
         connect('cap',self.layer2.C,self.layer2.D)

      if based:
         connect('cap',self.layer1.B,self.layer1.A)

class eth_layer(object):
   def __init__(self,name):
      self.up=self.eth_up('up')
      self.down=self.eth_down('down')
      self.A=self.up.A
      self.B=self.down.B
      self.C=self.up.B
      self.D=self.down.A

   class eth_up(duplex):
       def inspectA(self,stream,name):
          stream=stream.decode("HEX")
          stream=Ether(stream)[IP]
          stream=str(stream).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream=stream.decode("HEX")
          stream=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/IP(stream)
          stream=str(stream).encode("HEX")
          return stream

   class eth_down(duplex):
       def inspectA(self,stream,name):
          stream=stream.decode("HEX")
          stream=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/IP(stream)
          stream=str(stream).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream=stream.decode("HEX")
          stream=Ether(stream)[IP]
          stream=str(stream).encode("HEX")
          return stream

class ip_layer(object):
   def __init__(self,name):
      self.up=self.ip_up('up')
      self.down=self.ip_down('down')
      self.A=self.up.A
      self.B=self.down.B
      self.C=self.up.B
      self.D=self.down.A


   class ip_up(duplex):
       def inspectA(self,stream,name):
          stream=stream.decode("HEX")
          stream=IP(stream)[UDP]
          stream=str(stream).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream=stream.decode("HEX")
          stream=IP()/UDP(stream)
          stream=str(stream).encode("HEX")
          return stream

   class ip_down(duplex):
       def inspectB(self,stream,name):
          stream=stream.decode("HEX")
          stream=IP(stream)[UDP]
          stream=str(stream).encode("HEX")
          return stream

       def inspectA(self,stream,name):
          stream=stream.decode("HEX")
          stream=IP()/UDP(stream)
          stream=str(stream).encode("HEX")
          return stream

class udp_layer(object):
   def __init__(self,name):
      self.up=self.udp_up('up')
      self.down=self.udp_down('down')
      self.A=self.up.A
      self.B=self.down.B
      self.C=self.up.B
      self.D=self.down.A

   class udp_up(duplex):
       def inspectA(self,stream,name):
          stream=stream.decode("HEX")
          stream=UDP(stream)
          stream=stream.payload
          return stream

       def inspectB(self,stream,name):
#          stream=stream.decode("HEX")
          stream=UDP()/stream
          stream=str(stream).encode("HEX")
          return stream

   class udp_down(duplex):
       def inspectB(self,stream,name):
          stream=stream.decode("HEX")
          stream=UDP(stream)
          stream=stream.payload
          return stream

       def inspectA(self,stream,name):
#          stream=stream.decode("HEX")
          stream=UDP()/stream
          stream=str(stream).encode("HEX")
          return stream

class tcp_layer(object):
   def __init__(self,name):
      self.up=self.tcp_up('up')
      self.down=self.tcp_down('down')
      self.A=self.up.A
      self.B=self.down.B
      self.C=self.up.B
      self.D=self.down.A

   class tcp_up(duplex):
       def inspectA(self,stream,name):
          stream=stream.decode("HEX")
          stream=TCP(stream)
          stream=stream.payload
          return stream

       def inspectB(self,stream,name):
#          stream=stream.decode("HEX")
          stream=TCP()/stream
          stream=str(stream).encode("HEX")
          return stream

   class udp_down(duplex):
       def inspectB(self,stream,name):
          stream=stream.decode("HEX")
          stream=TCP(stream)
          stream=stream.payload
          return stream

       def inspectA(self,stream,name):
#          stream=stream.decode("HEX")
          stream=TCP()/stream
          stream=str(stream).encode("HEX")
          return stream



