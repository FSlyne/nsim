from scapy.all import *

eth = Ether()
packet = IP(dst="192.168.1.114")
icmp = packet/ICMP()/"Helloooo!"

hexdump(icmp)

frame=Ether()/IP()/UDP()/"This is a test message"

frame.time=0.001

wrpcap('packet.pcap',frame)

stream = str(frame).encode("HEX")
print stream

### Transmit the Frame

## decode
eth=Ether(stream.decode("HEX"))
eth.show()
exit()
ip=eth[IP]
ip.show()
udp=ip[UDP]
udp.show()
