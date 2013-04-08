'''
Created on 2013-3-28

@author: zhangjiaqin
'''
import time
import order
class Echo(object):
    def excute(self, protocol, header, id, params):
        echo = order.Echo(id)
        echo.excute(protocol, params)