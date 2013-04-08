# -*- coding: utf-8 -*-
'''
Created on 2013-3-28

@author: zhangjiaqin
'''
from xml.dom import minidom
class Order(object):
    _id = 0
    def __init__(self, ack_id, name = 'default'):
        self._doc = minidom.Document()
        methods = self._doc.createElement("methods")
        self._doc.appendChild(methods)
        method = self._doc.createElement("method")
        methods.appendChild(method)
        name_n = self._doc.createElement('name')
        name_n.setAttribute('id', repr(Order._id))
        method.appendChild(name_n)
        name_txt = self._doc.createTextNode(name)
        name_n.appendChild(name_txt)
        self._params = self._doc.createElement('params')
        method.appendChild(self._params)
        self._ack_id = ack_id
        
    def buildOrder(self):
        '''
        将生成命令xml写在order基类 方便其他命令复用
        '''
        xml = self._doc.toxml()
        self._order_txt = u'protocol:default\rversion:1.0\rpub-key:\rsize:%d\rcmd-id:%s\r%s'%(len(xml), self._ack_id, xml)
        self._order_txt = self._order_txt.encode('utf-8')
    def prepare(self, params):
        pass
    def excute(self, protocol, params = ''):
        Order._id += 1
        self.prepare(params)
        self.buildOrder()
        protocol.sendData(self._order_txt)
        
class Echo(Order):
    def __init__(self, ack_id):
        super(Echo, self).__init__(ack_id, "Echo")
    def prepare(self, params):
        for node in params[0].childNodes:
            if node.nodeType == node.ELEMENT_NODE:
                self._params.appendChild(node)

            
    
        
        