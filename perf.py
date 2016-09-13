import queue
import redis

hostname = '127.0.0.1'
port = '6379'

r = redis.Redis(host=hostname,port=port )

pattern="pkt:*"
l=list(r.scan_iter(match=pattern))
l=r.keys(pattern)
l.sort()
sa=sb=0 # send times
ra=rb=0 # receive times
scount= rcount =1
delay =0; jcount=0; jtotal=0
for e in l:
   sb=sa;rb=ra
   try:
      sa=float(r.hget(e,"sendtime"))
      ra=float(r.hget(e,"recvtime"))
      scount+=1
   except:
      continue
   if not ra:
      continue
   rcount+=1
   delay+=ra-sa
#   print ra-sa
   if not ra == 0:
      jitter=(sa-ra)-(sb-rb)
      jtotal+=jitter
#      print e,sa,ra,sb,rb,sa-ra, sb-rb,jitter,ra-sa
      jcount+=1
ploss=scount-rcount
print "Send Count :%d, Receive Count :%d, Jitter Count:%d" % (scount, rcount, jcount)
print "packet loss %d (%0.1f%%)" % (ploss,(ploss)/scount)
print "average jitter",jtotal/jcount
print "average delay",delay/rcount
