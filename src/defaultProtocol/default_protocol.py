# -*- coding: utf-8 -*-
'''
Created on 2013-3-26

@author: zhangjiaqin
'''
from zope.interface import  implements
from twisted.internet.protocol import Factory, Protocol
from twisted.internet import reactor, interfaces, defer
from xml.dom import minidom
import threading
import re
import time
import copy
import command
from exceptions import Exception

class ProtocolHeader(object):
    _max_header_len = 4 * 1024
    _protocol_key = "protocol"
    def __init__(self):
        self._got_header = False
        self._pro_name = ""
        self._pro_ver = ""
        self._pro_pub_key = ""
        self._cmd_id = ""
        self._cmd_size = 0
            
class DefaultProtocol(Protocol):
    '''
   由xml组成的命令式协议
    '''
    _total_endpoint = 0
    def __init__(self):
        self._header = ProtocolHeader()
        self._data = ""
        self._data_lock = threading.Lock()
        self._send_lock = threading.Lock()
        # for test
        self._total_cmd = 0
        self._total_send = 0
        self._total_send_n = 0
        self._total_get_n = 0
        self._beg_tm = time.time()


        
    def dataReceived(self, data):
        self._total_get_n += len(data)
        reactor.callInThread(self.parsePro, data)
        
    def connectionMade(self):
        DefaultProtocol._total_endpoint += 1
        print "online ", self.transport.getPeer().type, self.transport.getPeer().host, self.transport.getPeer().port
        print 'total connection: %d'%DefaultProtocol._total_endpoint

        
        
    def connectionLost(self, reason):
        DefaultProtocol._total_endpoint -= 1
        print "offline ", reason.getErrorMessage(), self.transport.getPeer().type, self.transport.getPeer().host, self.transport.getPeer().port
        print 'total send %d, %d, total get %d, %d'%(self._total_send, self._total_send_n, self._total_cmd, self._total_get_n)
    def peerInfo(self):
        return (self.transport.getPeer().host, self.transport.getPeer().port)
    
    def sendData(self, data):
        #reactor.callFromThread( self.transport.write, data)
        #self.transport.write( data )
        #reactor.wakeUp()
        #for testing
        self._send_lock.acquire()
        self.transport.write( data )
        self._total_send += 1
        self._total_send_n += len(data)
 #       if self._total_send % 10 == 0:
 #           print self.peerInfo(), self._total_send, time.time()-self._beg_tm
        self._send_lock.release()
    def dispatchCommand(self, header, xml):
        try:
            doc = minidom.parseString(xml)
            method = doc.getElementsByTagName("method")
            for cmd in method:
                try:
                    name = cmd.getElementsByTagName("name")
                    params = cmd.getElementsByTagName("params")
                    cls_cmd = getattr(command, name[0].firstChild.data, None)
                    if cls_cmd is not None:
                        cls_cmd().excute(self,
                             header, name[0].attributes['id'].value, params)
                        #for testing
                        self._data_lock.acquire()
                        self._total_cmd += 1
                        if self._total_cmd % 50 == 0:
                            print self.peerInfo(), self._total_cmd, time.time()-self._beg_tm
                            self._beg_tm = time.time()
                        self._data_lock.release()
                    else:
                        print "unkown command: %s"%name[0].firstChild.data
                except Exception, e:
                    print "exception : %s"%cmd.toxml()
                    print e
        except Exception, e:
            print e, 'xml is invalid'
    def parsePro(self, data):
        self._data_lock.acquire()
        self._data += data
        self._data_lock.release()
        
        while True:
            self._data_lock.acquire()
            if not self._header._got_header:
                ret = re.match("(.|\n)*protocol:(?P<p>(.|\n)*)\r{0,1}\nversion:(?P<v>(.|\n)*)\r{0,1}\npub-key:(?P<pkey>(.|\n)*)\r{0,1}\nsize:(?P<size>(.|\n)*)\r{0,1}\ncmd-id:(?P<cmd>.*)\r{0,1}\n(?P<data>(.|\n)*)",
                          self._data)       
                if not ret:
                    if len(self._data) >= ProtocolHeader._max_header_len: 
                        while True:
                            index = self._data.find(ProtocolHeader._protocol_key)
                            if index >= 0:
                                self._data = self._data[index + len(ProtocolHeader._protocol_key):]
                            else:
                                self._data = self._data[len(self._data) - len(ProtocolHeader._protocol_key):]
                                break
                    self._data_lock.release()
                    break
                else:
                    try:
                        d = ret.groupdict()
                        self._data = d['data']
                        self._header._got_header = True
                        self._header._cmd_id = d['cmd']
                        self._header._cmd_size = int(d['size'])
                        self._header._pro_name = d['p']
                        self._header._pro_pub_key = d['pkey']
                        self._header._pro_ver = d['v']
                    except ValueError:
                        self._header._got_header = False
                        print "size isn't int: %s"%d['size']
            if self._header._got_header and self._header._cmd_size <= len(self._data):
                try:
                    header = copy.deepcopy(self._header)
                    xml = self._data[:self._header._cmd_size]
                    self._data = self._data[self._header._cmd_size:]
                    self._header._got_header = False
                except Exception, e:
                    print e
                    self._data = self._data[self._header._cmd_size:]
                    self._header._got_header = False
                finally:
                    self._data_lock.release()
                self.dispatchCommand(header, xml)
                
            else:
                self._data_lock.release()
                break
                                     
class DefaultFactory(Factory):
    
    def buildProtocol(self, addr):
        return DefaultProtocol()