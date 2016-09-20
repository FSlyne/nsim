from scapy.all import *
from queue import *
import random
import time
from Queue import *

host = '127.0.0.1'
port = '6379'

class BadPacketError(Exception):
    pass

def get_payload(packet):
    while not isinstance(packet, TCP):
        packet = packet.payload
    return packet.payload

class TCPSocket(process):
    import random
    import string
    def __init__(self, listener, debug=False):
        self.state = "CLOSED"
        self.debug = debug
    
        self.use_fastretransmit = True
        self.window = self.reqwindow = self.mss =1000
        self.cwnd = self.mss
        self.ssthresh = self.mss * 5
        self.congestion_state = 0 # slow start =0, congestion avoid = 1, fast recovery = 2

        self.src_ip = listener.ip_address
        self.recv_buffer = ""
        self.listener = listener
        self.seq = self._generate_seq()
        self.seq = 1234
        self.ackvol=0
        self.last_ack_sent = 0
        self.name="TCPsocket"
        process.__init__(self,0)
        self.actual_ack = 0
        # self.r = redis.Redis(host=host,port=port )
        self.r =redis.Redis(unix_socket_path='/var/run/redis/redis.sock')
        self.xid = self.randtoken()
        self.last_ack_recv = 0
        self.bulksend()
        self.statscollector()
        self.garbage=Queue()
        self.ackmgr()
        self.cleanup()

        self.retranQ = retransmission(callback=self.sendseq, xid=self.xid,congmgr=self.congestion_mgr)

    def randtoken(self,size=6, chars=string.ascii_uppercase + string.digits):
      return ''.join(self.random.choice(chars) for _ in range(size))

    @threaded
    def cleanup(self):
       while True:
          key=self.garbage.get()
          r.delete(key)

    @threaded
    def statscollector(self):
      f = open("tcpstats_%s.log" % self.listener.ip_address, "w")
      f.write("ms\tcwnd\tssthresh\n")
      while True:
         self.wait100mstick()
         f.write("%0.3f\t%s\t%s\n" %(float(self.getsimtime()),str(self.window),str(self.ssthresh)))
      f.close()
        
    @staticmethod
    def _has_load(packet):
        payload = get_payload(packet)
        if isinstance(payload, Padding):
            return False
        return bool(payload)

    def _set_dest(self, host, port):
        self.dest_port = port
        self.dest_ip = host
        self.ip_header = IP(dst=self.dest_ip, src=self.src_ip)

    def connect(self, host, port):
        self._set_dest(host, port)
        self.src_port = self.listener.get_port()
        self.listener.open(self.src_ip, self.src_port, self)
        self._send_syn()

    def bind(self, host, port):
        # Right now, listen for only one connection.
        self.src_ip = host
        self.src_port = port
        self.listener.open(self.src_ip, self.src_port, self)
        self.state = "LISTEN"

    @staticmethod
    def _generate_seq():
        return random.randint(0, 100000)

    # congestion states: slow start =0, congestion avoid = 1, fast recovery = 2
    def congestion_mgr(self,typ=0): # 0 = timeout, 1 = dup, 2 = non-dup, 3 = double-dup
       lock,now=self.lock()
       cong=self.congestion_state; ssthresh = self.ssthresh; window = self.window
       if self.use_fastretransmit:
          if self.congestion_state == 0: # slow start
             if typ == 2: # non-dup
                self.window+=self.mss
                if self.window >= self.ssthresh:
                   self.congestion_state = 1
             else:
                self.congestion_state == 0
                self.window = self.mss
          elif self.congestion_state == 1: # avoid
             if typ == 2: # non-dup
                if self.ackvol >= self.window:
                   self.window+=self.mss
                self.congestion_state = 1
             elif typ == 0:#timeout
                self.ssthresh = int(self.window/2)
                self.window = self.ssthresh + 3*self.mss
             elif typ == 1: # dup
                self.ssthresh = int(self.window/2)
                self.window = self.mss
                self.congestion_state = 2
             else:
                self.window = self.mss
          elif self.congestion_state == 2: # fast_recovery
             if typ == 2: # non-dup
                self.ssthresh = self.window
             elif typ == 1: # dup
                self.window +=self.window
       else:
          if self.congestion_state == 0: # slow start
             if typ == 2: # non-dup
                self.window+=self.mss
                if self.window >= self.ssthresh:
                   self.congestion_state = 1
             else:
                self.congestion_state == 0
                self.window = self.mss
          elif self.congestion_state == 1: # avoid
             if typ == 2: # non-dup
#                 print "ack vol =",self.ackvol,self.window
                 if self.ackvol >= self.window:
                    self.window+=self.mss
#                self.window = int(self.window+1/self.window)
#                 self.window+=1
             else:
                self.window = self.mss
          else:
             pass
       if not cong == self.congestion_state:
          print "Congestion state has changed from %d to %d " % (cong, self.congestion_state)
       if not ssthresh == self.ssthresh:
          print "SSthresh has changed from %d to %d" % (ssthresh, self.ssthresh)
       if not window == self.window:
          print "Congestion window has changed from %d to %d" % (window, self.window)
       self.unlock(lock)


    @threaded
    def bulksend(self):
       while True:
          payload=self.r.blpop("inbuf:"+self.xid)[1]
          self.r.set("seq:"+self.xid+":"+str(self.seq),payload)
          self.retranQ.add(self.seq)
          self._send_ack(load=payload, flags='')
          self.seq += len(payload)
#          print len(payload),self.seq,self.last_ack_recv,self.window
          while True:
             diff = len(payload)+self.seq - self.last_ack_recv
             # don't send if self.seq > self.last_ack_recv + min(cwnd, rwnd)
             if len(payload)+self.seq - self.last_ack_recv >= self.window*1.4:
                self.waitfor(1)
             else:
#                print "++++",self.seq,self.window,diff
                break

    def sendseq(self,seq,flags=""):
#        print "sendseq: ",seq
        payload=self.r.get("seq:"+self.xid+":"+str(seq))
        if not payload:
           return

        # Window Scaling RFC 1323
        rewin,shft = self.enscale(self.window)
        
        packet = TCP(dport=self.dest_port,
                     sport=self.src_port,
                     seq=int(seq),
                     ack=self.last_ack_sent,
                     flags=flags,
                     window=rewin,
                     options=[('WScale', shft)])
        # Add the IP header
        full_packet = Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/self.ip_header / packet / payload
        self.listener.send(full_packet)
                

    def _send(self, flags="", load=None):
        """Every packet we send should go through here."""
        # Window Scaling RFC 1323
        rewin,shft = self.enscale(self.window)

        packet = TCP(dport=self.dest_port,
                     sport=self.src_port,
                     seq=self.seq,
                     ack=self.last_ack_sent,
                     flags=flags,
                     window=rewin,
                     options=[('WScale', shft)])
        full_packet = Ether(src='00:00:00:00:00:00',dst='00:00:00:00:00:00')/self.ip_header / packet
        # Add the payload
        if load:
            full_packet = full_packet / load
        # Send the packet over the wire
        self.listener.send(full_packet)
        # Update the sequence number with the number of bytes sent
#        if load is not None:
#            self.seq += len(load)

    def _send_syn(self):
        self.state = "SYN-SENT"
        self._send(flags="S")

    def _send_ack(self, flags="", load=None):
        self._send(flags=flags + "A", load=load)

    def close(self):
        if self.state == "CLOSED":
            return
        self.state = "FIN-WAIT-1"
        self._send_ack(flags="F")

    @staticmethod
    def next_seq(packet):
        # really not right.
        tcp_flags = packet.sprintf("%TCP.flags%")
        if TCPSocket._has_load(packet):
            return packet.seq + len(packet.load)
        elif 'S' in tcp_flags or 'F' in tcp_flags:
            return packet.seq + 1
        else:
            return packet.seq

    def _close(self):
        self.state = "CLOSED"
        self.listener.close(self.src_ip, self.src_port)

    def enscale (self,window):
        shft = 0
        rewin = window
        for shft in range(0,15):
           if rewin <= 65535:
              break
           rewin = rewin >> 1
        return rewin,shft

    def descale(self,rewin,shft):
        return rewin << shft

    def find_tcp_option(self,key, default,options):
         for opt in options:
            if opt == key:
                return None
            if opt[0] == key:
                return opt[1]
         return default


    def handle(self, packet):
        # Handle incoming packets
        lock,now=self.lock()
        if self.last_ack_sent and self.last_ack_sent != packet.seq:
            if self.debug:
               print "+++++++ Handle Dropping Packet ++++++"
               print self.last_ack_sent,  packet.seq
#            return

        self.last_ack_sent = max(self.next_seq(packet), self.last_ack_sent)
        self.last_ack_recv = packet.ack
        self.cwnd = self.descale(packet.window,self.find_tcp_option('WScale',0,packet[TCP].options))

        recv_flags = packet.sprintf("%TCP.flags%")

        if self.debug:
           print "++++++++ Handle +++++++++++"
           packet.show()

        # Handle all the cases for self.state explicitly
        if self._has_load(packet):
#            self.recv_buffer += packet.load # Officially received ????
            self.r.rpush("recvbuf:"+self.xid,packet.load)
            packet.show()
            self.r.set("ack:"+self.xid+":"+"%010d"% packet.seq,len(packet.load))
#               self._send_ack()
        elif "R" in recv_flags:
            self._close()
        elif "S" in recv_flags:
            if self.state == "LISTEN":
                self.state = "SYN-RECEIVED"
                self._set_dest(packet.payload.src, packet.sport)
                self._send_ack(flags="S")
            elif self.state == "SYN-SENT":
                self.seq += 1
                self.state = "ESTABLISHED"
                self._send_ack()
        elif "F" in recv_flags:
#            self.retranQ.clearall()
            if self.state == "ESTABLISHED":
                self.seq += 1
                self.state = "LAST-ACK"
                self._send_ack(flags="F")
            elif self.state == "FIN-WAIT-1":
                self.seq += 1
                self._send_ack()
                self._close()
        elif "A" in recv_flags:
            if self.state ==  "ESTABLISHED":
               self.ackvol=self.retranQ.cleardown(packet.ack)
               self.congestion_mgr(2)
#               self.retranQ.remove(packet.ack-1)
               self.last_ack_recv = packet.ack
            if self.state == "SYN-RECEIVED":
                self.state = "ESTABLISHED"
            elif self.state == "LAST-ACK":
                self._close()
        else:
            raise BadPacketError("Oh no!")
        self.unlock(lock)

    def send(self, payload):
        # Block
        while self.state != "ESTABLISHED":
#            time.sleep(0.001)
            self.waitfor(1)
        # Do the actual send
        self.r.rpush("inbuf:"+self.xid,str(payload))
#        self.waitfor(1)
#        self._send_ack(load=payload, flags="P")


    def recv(self, size, timeout=None):
        recv=''
        if self.state in ["CLOSED", "LAST-ACK"]:
           return recv 
        recv = self.r.blpop("recvbuf:"+self.xid)[1]
        return recv

    @threaded
    def ackmgr(self):
      while True:
        lock,now=self.lock()
        x=[]; y=[]
        l = self.r.keys(pattern="ack:"+self.xid+":*")
        l.sort()
        print l
        for e in l:
           try:
              seq=int(e.split(':')[-1:][0].lstrip("0"))
              val=int(self.r.get("ack:"+self.xid+":"+"%010d" % seq))
           except:
              print e
              print "Seq Error",seq
           x.append(seq); y.append(seq+val)
        if x:
#           print "*:",x,"+:",y
           start=end=x.pop(0)
           while True:
              if not x:
                break
              w = x.pop(0)
              if not w:
                break
              v = y.pop(0)
              if not v:
                break
              if w == v:
                end = w
#           print "ack window: ",end-start,end, start
           if end-start >= self.cwnd:
              self.ack = end+1
              self._send_ack()
              for e in l:
                 seq=int(e.split(':')[-1:][0].lstrip("0"))
                 if seq <= end:
#                    print "deleting:", "ack:"+self.xid+":"+"%010d" % seq
                    key="ack:"+self.xid+":"+"%010d" % seq
                    self.garbage.put(key)
#                    self.r.delete(key)
        self.unlock(lock)
        self.waitfor(5)

class retransmission(process):
    def __init__(self,callback='',congmgr='',xid='',queue='retransmission',rto=3.000):
       self.r = redis.Redis(host=host,port=port )
       self.xid=xid
       self.queue = queue
       self.queue2 = queue+"2"
       self.rto = rto
       self.gap = rto*0.1
       self.callback=callback
       self.congmgr=congmgr
       self.name='tcpretransmission'
       self.garbage=Queue()
       process.__init__(self,0)
       self.routine()
       self.routine2()
       self.cleanup()

    @threaded
    def cleanup(self):
       while True:
          key=self.garbage.get()
          r.delete(key)

    @threaded
    def routine(self):
       while True:
          for seq,tick in self.r.zrangebyscore(self.queue, 0 ,str(float(self.getsimtime())+self.gap),withscores=True):
             self.congmgr(0) # signal a timeout
             print "timeout - 1",seq,tick,self.getsimtime()
             self.callback(seq)
             self.remove(seq)
             self.add2(seq)
          else:
             self.waitfor(1)

    @threaded
    def routine2(self):
       while True:
          for seq,tick in self.r.zrangebyscore(self.queue2, 0 ,str(float(self.getsimtime())+self.gap),withscores=True):
             self.congmgr(0) # signal a timeout
             print "timeout - 2"
             self.callback(seq)
             self.remove2(seq)
#             self.add(seq)
          else:
             self.waitfor(1)

    def remove(self,seq):
       key="seq:"+self.xid+":"+str(seq)
       try:
         size=int(len(self.r.get(key)))
         self.garbage.put(key)
       except:
         size=0
       return self.r.zrem(self.queue, str(seq)),size

    def remove2(self,seq):
       "seq:"+self.xid+":"+str(seq)
       try:
         size=int(len(self.r.get(key)))
         self.garbage.put(key)
       except:
         size=0
       return self.r.zrem(self.queue2, str(seq)),size

    def add(self,seq):
       later = float(self.rto)+float(self.getsimtime())
       self.r.zadd(self.queue,str(seq),str(later))

    def add2(self,seq):
       later = float(self.rto)+float(self.getsimtime())
       self.r.zadd(self.queue2,str(seq),str(later))


    def cleardown(self,threshseq):
       print "received threshseq ",threshseq,self.getsimtime()
       tally=0
       for seq,tick in self.r.zrangebyscore(self.queue, 0 ,str(100000),withscores=True):
         if int(seq) <= int(threshseq):
            status,size = self.remove(seq)
            tally+=size
       for seq,tick in self.r.zrangebyscore(self.queue2, 0 ,str(100000),withscores=True):
         if int(seq) <= int(threshseq):
            status,size =self.remove2(seq)
            tally+=size
       return tally

    def clearall(self):
       for seq,tick in self.r.zrangebyscore(self.queue, 0 ,str(1000000000),withscores=True):
           self.remove(seq)
       for seq,tick in self.r.zrangebyscore(self.queue2, 0 ,str(1000000000),withscores=True):
           self.remove2(seq)



