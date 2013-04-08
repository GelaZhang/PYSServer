# -*- coding: utf-8 -*-
'''
Created on 2013-3-26

@author: zhangjiaqin
'''

from twisted.internet import iocpreactor
import os
if os.name == 'nt':
    try:
        iocpreactor.install()
    except:
        print "install iocpreactor exception"
from twisted.internet import reactor, defer
from defaultProtocol.default_protocol import DefaultFactory
class PYSServer(object):
    '''
    '''
    def __init__(self):
        pass
        
    def run(self):
        #reactor.suggestThreadPoolSize(30)
        reactor.listenTCP(5055, DefaultFactory())
        reactor.run()
        
if __name__ == "__main__":
    
    
    service = PYSServer()
    service.run()