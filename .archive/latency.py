from network import *


sched=scheduler(tick=0.001,finish=10)

LQ=LatencyQueue(latency=10)

LQ.put("ABD")
LQ.put("ABC")
LQ.put("XVY")
LQ.put("123")
LQ.put("111")


sched.process()
