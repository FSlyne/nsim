from queue import *
from scapy.all import *

class MPLS(Packet):
   name = "MPLS"
   fields_desc =  [ BitField("label", 3, 20),
                    BitField("cos", 0, 3),
                    BitField("s", 1, 1),
                    ByteField("ttl", 0)  ]


bind_layers(Ether, MPLS, type = 0x8847) # Marks MPLS
bind_layers(MPLS, MPLS, bottom_of_label_stack = 0) # We're not at the bottom yet
bind_layers(MPLS, IP)

class transmission(duplex):
   def __init__(self, *args, **kwargs):
      self.name=args[0]
      self.capacity = kwargs.get('capacity',0) # Mbps
      self.trace = kwargs.get('trace',False) # turn on/off pcap tracing
      if 'capacity' in kwargs:
         del kwargs['capacity']
      if 'trace' in kwargs:
         del kwargs['trace']
      if self.trace:
         self.pcapw=PcapWriter(self.name+'.pcap')
      if self.capacity >0:
         kwargs['ratelimit'] = 1000000*self.capacity
      kwargs['ratio'] = 2 # 2 chars in queue eqiv. 1 byte of application data
      super(transmission, self).__init__(*args, **kwargs)

   def inspectA(self,stream,name):
      if self.trace:
         frame=Ether(stream.decode("HEX"))
         frame.time=float(self.nw())
         self.pcapw.write(frame)
      return stream

   def inspectB(self,stream,name):
      if self.trace:
         frame=Ether(stream.decode("HEX"))
         frame.time=float(self.nw())
         self.pcapw.write(frame)
      return stream


class eth_switch(object):
   def __init__(self,name):
      self.up=self.eth_up('up')
      self.down=self.eth_down('down')
      self.A=self.up.A
      self.B=self.down.B

      connect('cap',self.up.B,self.down.A)

   class eth_up(duplex):
       def inspectA(self,stream,name):
          stream1=stream.decode("HEX")
          eth=Ether(stream1)
          ip=eth[IP]
          stream=str(ip).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream1=stream.decode("HEX")
          stream2=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/IP(stream1)
          stream=str(stream2).encode("HEX")
          return stream

   class eth_down(duplex):
       def inspectA(self,stream,name):
          stream1=stream.decode("HEX")
          stream2=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/IP(stream1)
          stream=str(stream2).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream1=stream.decode("HEX")
          eth=Ether(stream1)
#          eth.show()
          ip=eth[IP]
          stream=str(ip).encode("HEX")
          return stream

class router(object):
   def __init__(self,name):
      self.up=self.route_up('up')
      self.down=self.route_down('down')
      self.A=self.up.A
      self.B=self.down.B

      connect('cap',self.up.B,self.down.A)

   class route_up(duplex):
       def inspectA(self,stream,name):
          stream1=stream.decode("HEX")
          eth=Ether(stream1)
          ip=eth[IP]
          udp=ip[UDP]
          stream=str(udp).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream1=stream.decode("HEX")
          stream2=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/IP()/UDP(stream1)
          stream=str(stream2).encode("HEX")
          return stream

   class route_down(duplex):
       def inspectA(self,stream,name):
          stream1=stream.decode("HEX")
          stream2=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/IP()/UDP(stream1)
          stream=str(stream2).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream1=stream.decode("HEX")
          eth=Ether(stream1)
          ip=eth[IP]
          udp=ip[UDP]
          stream=str(udp).encode("HEX")
          return stream

class mpls_switch(object):
   def __init__(self,name,labelA=0,labelB=0):
      self.up=self.mpls_up('up')
      self.down=self.mpls_down('down')
      self.A=self.up.A
      self.B=self.down.B

      connect('cap',self.up.B,self.down.A)

   class mpls_up(duplex):
       def __init__(self,*args, **kwargs):
          self.labelA = kwargs.get('labelA')
          self.labelB = kwargs.get('labelB')
          if 'labelA' in kwargs:
             del kwargs['labelA']
          if 'labelB' in kwargs:
             del kwargs['labelB']
          super(mpls_switch.mpls_up, self).__init__(*args, **kwargs)
#          duplex.__init__(self,'name')

       def inspectA(self,stream,name):
          stream1=stream.decode("HEX")
          eth=Ether(stream1)
          if self.labelA > 0:
             mpls=eth[MPLS]
             ip=mpls[IP]
          else:
             ip=eth[IP]
          stream=str(ip).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream1=stream.decode("HEX")
          if self.labelB > 0:
             stream2=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/MPLS()/IP(stream1)
          else:
             stream2=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/IP(stream1)
          stream=str(stream2).encode("HEX")
          return stream

   class mpls_down(duplex):
       def __init__(self,*args, **kwargs):
          self.labelA = kwargs.get('labelA')
          self.labelB = kwargs.get('labelB')
          if 'labelA' in kwargs:
             del kwargs['labelA']
          if 'labelB' in kwargs:
             del kwargs['labelB']
          super(mpls_switch.mpls_down, self).__init__(*args, **kwargs)

       def inspectA(self,stream,name):
          stream1=stream.decode("HEX")
          if self.labelA:
             stream2=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/MPLS()/IP(stream1)
          else:
             stream2=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/IP(stream1)
          stream=str(stream2).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream1=stream.decode("HEX")
          eth=Ether(stream1)
          if self.labelA:
             mpls=eth[MPLS]
             ip=mpls[IP]
          else:
             ip=eth[IP]
          stream=str(ip).encode("HEX")
          return stream

class vlan_switch(object):
   def __init__(self,name,vlanA=0,vlanB=0):
      self.up=self.vlan_up('up')
      self.down=self.vlan_down('down')
      self.A=self.up.A
      self.B=self.down.B

      connect('cap',self.up.B,self.down.A)

   class vlan_up(duplex):
       def __init__(self,*args, **kwargs):
          self.vlanA = kwargs.get('vlanA')
          self.vlanB = kwargs.get('vlanB')
          if 'vlanA' in kwargs:
             del kwargs['vlanA']
          if 'vlanB' in kwargs:
             del kwargs['vlanB']
          super(vlan_switch.vlan_up, self).__init__(*args, **kwargs)
#          duplex.__init__(self,'name')

       def inspectA(self,stream,name):
          stream1=stream.decode("HEX")
          eth=Ether(stream1)
          if self.vlanA > 0:
             vlan=eth[dot1Q]
             ip=vlan[IP]
          else:
             ip=eth[IP]
          stream=str(ip).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream1=stream.decode("HEX")
          if self.vlanB > 0:
             stream2=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/dot1Q()/IP(stream1)
          else:
             stream2=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/IP(stream1)
          stream=str(stream2).encode("HEX")
          return stream

   class vlan_down(duplex):
       def __init__(self,*args, **kwargs):
          self.vlanA = kwargs.get('vlanA')
          self.vlanB = kwargs.get('vlanB')
          if 'vlanA' in kwargs:
             del kwargs['vlanA']
          if 'vlanB' in kwargs:
             del kwargs['vlanB']
          super(vlan_switch.vlan_down, self).__init__(*args, **kwargs)

       def inspectA(self,stream,name):
          stream1=stream.decode("HEX")
          if self.vlanA:
             stream2=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/dot1Q()/IP(stream1)
          else:
             stream2=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/IP(stream1)
          stream=str(stream2).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream1=stream.decode("HEX")
          eth=Ether(stream1)
          if self.vlanA:
             vlan=eth[dot1Q]
             ip=vlan[IP]
          else:
             ip=eth[IP]
          stream=str(ip).encode("HEX")
          return stream



class host(object):
   def __init__(self,name,stack='udp'):
      self.up=self.eth_up('up')
      self.A=self.up.A
      self.B=self.up.B

   class eth_up(duplex):
       def inspectA(self,stream,name):
          eth=Ether(stream.decode("HEX"))
          ip=eth[IP]
          udp=ip[UDP]
#          stream=str(payload).encode("HEX")
          return udp.payload

       def inspectB(self,payload,name):
#          print "payload B:",payload
#          stream=payload.decode("HEX")
          frame=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/IP()/UDP(sport=1234,dport=2345)/payload
          stream=str(frame).encode("HEX")
          return stream

class router2(object):
   def __init__(self,name):
      self.layer1=eth_layer('ethernet_layer')
      self.layer2=ip_layer('ip_layer')
      self.A=self.layer1.A
      self.B=self.layer1.B
      self.C=self.layer2.C
      self.D=self.layer2.D

      connect('J1',self.layer1.C,self.layer2.A)
      connect('J2',self.layer2.B,self.layer1.D)

      connect('cap',self.layer2.C,self.layer2.D)

class mplsswitch(object):
   def __init__(self,name,labelA='',labelB=''):
      self.layer1=eth_layer('ethernet_layer')
      self.layer2=mpls_layer('mpls_layer',labelA,labelB)
      self.A=self.layer1.A
      self.B=self.layer1.B
      self.C=self.layer2.C
      self.D=self.layer2.D

      connect('J1',self.layer1.C,self.layer2.A)
      connect('J2',self.layer2.B,self.layer1.D)

      connect('cap',self.layer2.C,self.layer2.D)

class host2(object):
   def __init__(self,name,stack='udp'):
      self.block1=eth_block('ethernet_layer')
      self.block2=ip_block('ip_layer')
      if stack == 'udp':
        self.block3=udp_block('udp_layer')
      else:
        self.block3=tcp_block('tcp_layer')
      self.A=self.block1.A
      self.B=self.block3.B

      connect('J1',self.block1.B,self.block2.A)
      connect('J2',self.block2.B,self.block3.A)


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
   def __init__(self,name,upperlayer='ip'):
      self.up=self.eth_up('up',upperlayer)
      self.down=self.eth_down('down',upperlayer)
      self.A=self.up.A
      self.B=self.down.B
      self.C=self.up.B
      self.D=self.down.A

  
   class eth_up(duplex):
       def __init__(self,*args, **kwargs):
          self.upperlayer = kwargs.get('upperlayer')
          del kwargs['upperlayer']
          duplex.__init__(self,'name')

       def inspectA(self,stream,name):
          stream=stream.decode("HEX")
          if self.upperlayer == 'ip':
             stream=Ether(stream)[IP]
          else:
             stream=Ether(stream)[MPLS]
          stream=str(stream).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream=stream.decode("HEX")
          if self.upperlayer == 'ip':
             stream=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/IP(stream)
          else:
             stream=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/MPLS(stream)
          stream=str(stream).encode("HEX")
          return stream

   class eth_down(duplex):
       def __init__(self,*args, **kwargs):
          self.upperlayer = kwargs.get('upperlayer')
          del kwargs['upperlayer']
          duplex.__init__(self,'name')

       def inspectA(self,stream,name):
          stream=stream.decode("HEX")
          if self.upperlayer == 'ip':
             stream=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/IP(stream)
          else:
             stream=Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/MPLS(stream)
          stream=str(stream).encode("HEX")
          return stream

       def inspectB(self,stream,name):
          stream=stream.decode("HEX")
          if self.upperlayer == 'ip':
             stream=Ether(stream)[IP]
          else:
             stream=Ether(stream)[MPLS]
          stream=str(stream).encode("HEX")
          return stream

class eth_block(object):
   def __init__(self,name):
      self.up=self.eth_up('up')
      self.A=self.up.A
      self.B=self.up.B

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

class ip_block(object):
   def __init__(self,name):
      self.up=self.ip_up('up')
      self.A=self.up.A
      self.B=self.up.B


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

class udp_block(object):
   def __init__(self,name):
      self.up=self.udp_up('up')
      self.A=self.up.A
      self.B=self.up.B

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

class tcp_block(object):
   def __init__(self,name):
      self.up=self.tcp_up('up')
      self.A=self.up.A
      self.B=self.up.B

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


class tcp_layer(object):
   def __init__(self,name):
      self.up=self.tcp_up('up')
      self.A=self.up.A
      self.B=self.up.B

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

class mpls_layer(object):
   def __init__(self,name,labelA,labelB):
      self.up=self.mpls_up('up',labelA=labelA,labelB=labelB)

      self.down=self.mpls_down('down',labelA=labelA,labelB=labelB)
      self.A=self.up.A
      self.B=self.down.B
      self.C=self.up.B
      self.D=self.down.A

   class mpls_up(duplex):
       def __init__(self,*args, **kwargs):
          self.labelA = kwargs.get('labelA',234)
          self.labelB = kwargs.get('labelB',456)
          del kwargs['labelA']
          del kwargs['labelB']
#          super(mpls_layer.mpls_up, self).__init__(*args, **kwargs)
          duplex.__init__(self,'name')
  
       def inspectA(self,stream,name):
          try:
            stream=stream.decode("HEX")
            if self.labelA:
              stream=MPLS(stream)[IP]
            else:
              stream=Ether(stream)[IP]
            stream=str(stream).encode("HEX")
          except:
            print "Exception: ",stream
          return stream

       def inspectB(self,stream,name):
          try:
            stream=stream.decode("HEX")
            if self.labelA:
               stream=MPLS()/IP(stream)
            else: 
               stream=Ether()/IP(stream)
            stream=str(stream).encode("HEX")
          except:
            print "Exception: ",stream
          return stream

   class mpls_down(duplex):
       def __init__(self,*args, **kwargs):
          self.labelA = kwargs.get('labelA',234)
          self.labelB = kwargs.get('labelB',456)
          del kwargs['labelA']
          del kwargs['labelB']
#          super(mpls_layer.mpls_up, self).__init__(*args, **kwargs)
          duplex.__init__(self,'name')

       def inspectA(self,stream,name):
          try:
            stream=stream.decode("HEX")
            if self.labelA:
               stream=MPLS()/IP(stream)
            else:
               stream=Ether()/IP(stream)
            stream=str(stream).encode("HEX")
          except:
            print "Exception: ",stream
          return stream

       def inspectB(self,stream,name):
          try:
            stream=stream.decode("HEX")
            if self.labelA:
              stream=MPLS(stream)[IP]
            else:
              stream=Ether(stream)[IP]
            stream=str(stream).encode("HEX")
          except:
            print "Exception: ",stream
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



