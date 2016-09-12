import queue
import redis

hostname = '127.0.0.1'
port = '6379'

r = redis.Redis(host=hostname,port=port )

#unit='qsize'
#unit='now:bps'
# con2:connect1:now:bps
unit='queue'

def calcstats():
  l = r.keys(pattern='stats:*')
  m=[]
  for e in l:
    w=e.split(':')[:-1]
    w=":".join(w)
    m.append(w)
  for e in m:
    tally=0
    pattern=e+":*"
    l=r.keys(pattern)
    l.sort()
    l=l[-10:] # get the last 10 keys
    for f in l:
      try:
        b = r.get(f)
        tally+=int(b)
      except:
        pass
    f=e.split(':')
    unit=f[0]+'ps:'+f[1]+'ps:'+":".join(f[2:])
#    r.set("statsps:"+units+"ps:"+elem,tally)
 
    print unit,tally
  return

calcstats()

exit()


def get_elements(unit):
  global r
  l = r.keys(pattern='statsps:*')
  print l
  m=[]
  for e in l:
    print e
    w = e.split(':')[:-1]
    m.append(':'.join(w))
  return list(set(m))

elist=[]


elist=get_elements(unit)
elist.sort()

print elist

exit()

for e in elist:
  v=r.get(e+":"+unit)
  print e,v

exit()

for e in elist:
  print e
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

