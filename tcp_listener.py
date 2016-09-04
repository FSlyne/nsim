import random
import threading
from queue import *
from scapy.all import *

def threaded(fn):
    import threading
    def wrapper(*args, **kwargs):
        t=threading.Thread(target=fn, args=args, kwargs=kwargs)
        t.daemon=True
        t.start()
    return wrapper


class TCPListener(object):
    def __init__(self, recv, xmit, ip_address="127.0.0.1", debug=False):
        self.recv = recv
        self.xmit = xmit
        self.ip_address = ip_address
        self.debug = debug
        self.source_port = random.randint(12345, 50000)
        self.open_sockets = {}
        self.listen()

    def dispatch(self, pkt):
        if not isinstance(pkt.payload.payload, TCP):
            return
        ip, port = pkt.payload.dst, pkt.dport
#        if ip != self.ip_address:
#            return

#        if (ip, port) not in self.open_sockets:
#            reset = Ether(src='00:00:00:11:22:33',dst='00:00:00:22:33:44')/IP(src=ip, dst=pkt.payload.src) / TCP(seq=pkt.ack, sport=port, dport=pkt.sport, flags="R")
#            self.send(reset)
#            print "Resetting"
#            return
        try:
           conn = self.open_sockets[ip, port]
        except:
           print "Open Sockets Issue"
        conn.handle(pkt)

    def send(self, packet):
         # Send on the wire
         if self.debug:
            print "+++++ Sending Packets on Wire++++++++"
            packet.show()
         packet=str(packet).encode("HEX")
         self.xmit(packet)

    def get_port(self):
        # We need to return a new port number to each new connection
        self.source_port += 1
        return self.source_port

    def open(self, ip, port, conn):
        self.open_sockets[ip, port]  = conn

    def close(self, ip, port):
        del self.open_sockets[ip, port]

    @threaded
    def listen(self):
        while True:
           # listen on the wire
           packet=self.recv()
           packet=Ether(str(packet).decode("HEX"))
           if self.debug:
              print "+++++ Receiving Packets on Wire ++++++++"
              packet.show()
           self.dispatch(packet)

