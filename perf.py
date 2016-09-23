import queue
import redis

hostname = '127.0.0.1'
port = '6379'

def get_tally(elem):
   try:
     val=int(r.get("stats:"+str(elem)+":tally"))
   except:
     val=0
   return val

payloadsize=200
payloadtotal=0

r = redis.Redis(host=hostname,port=port )

pattern="pkt:*"
l=list(r.scan_iter(match=pattern))
l=r.keys(pattern)
l.sort()
start_time=sa=sb=0 # send times
end_time=ra=rb=0 # receive times
scount= rcount =1
delay =0; jcount=0; jtotal=0
for e in l:
   sb=sa;rb=ra
   try:
      sa,payloadsize=r.hget(e,"sendtime").split(":")
      sa=float(sa); payloadsize=int(payloadsize)
   except:
      sa=0.0
   try:
      ra=float(r.hget(e,"recvtime"))
   except:
      ra=0.0
   scount+=1
   if not ra:
      continue
   else:
      payloadtotal+=payloadsize
   rcount+=1
   delay+=ra-sa
   jitter=(sa-ra)-(sb-rb)
   jtotal+=jitter
#   print e,sa,ra,sb,rb,sa-ra, sb-rb,jitter,ra-sa
   jcount+=1
   end_time=max(end_time,ra)
ploss=scount-rcount
duration=end_time-start_time
print "Send Count :%d, Receive Count :%d, Jitter Count:%d" % (scount, rcount, jcount)
print "packet loss %d (%0.3f %%)" % (ploss,ploss*100.0/scount)
print "average jitter %0.3f ms" % float(jtotal/jcount)
print "average delay %0.5f ms" % float(delay/rcount)
print "Total Time %0.3f sec, Throughput %0.3f per second" % (float(duration),float(payloadtotal*8/duration))

rtlmt=get_tally('rtlmt')
bkprs=get_tally('bkprs')
pktdrp_mxq=get_tally('pktdrp_mxq')
pktdrp_age=get_tally('pktdrp_age')
print 
print "Packets stats: Rate Limit %d, Back Pressure %d, Dropped (MXQ) %d, Dropped (aged) %d" % (rtlmt,bkprs,pktdrp_mxq,pktdrp_age)
