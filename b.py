from ona.zmqbroker import *

loghost='127.0.0.1'
logbrokerport=10002; logpubsubport=10003
logtopic='Logger'

class zmqsub(zmqSubscriber):
  def process(self,mst,msg):
    print "timestamp=%s, msg=%s" %(mst,msg)

zmqBroker(brokerport=logbrokerport,pubsubport=logpubsubport)
zmqsub(logtopic,pubsubhost=loghost,pubsubport=logpubsubport)

zmqsender=zmqSender(logtopic,brokerhost=loghost,brokerport=logbrokerport)
zmqsender.tx("LoggerStarting")

while True:
   time.sleep(1)

