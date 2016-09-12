import queue
import redis

hostname = '127.0.0.1'
port = '6379'

r = redis.Redis(host=hostname,port=port )

unit='qsize'
# unit='bps'
# unit='queue'

def get_elements(unit):
  global r
  l = r.keys(pattern='*:'+unit)
  m=[]
  for e in l:
    w = e.split(':')[:-2]
    m.append(':'.join(w))
  return list(set(m))

elist=[]

elist=get_elements(unit)
elist.sort()

for e in elist:
  l=r.keys(pattern=e+':*:'+unit)
  for m in l:
     v=r.get(m)
     print m,v

exit()

l.sort()
y = l[:-2]
print y
exit
bits=0
for e in y:
   b = r.get(e)
   bits+=int(r.get(e))
   print e,b,bits

