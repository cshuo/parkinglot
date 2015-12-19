# coding: utf-8
from threading import Thread
import socket
from Queue import Queue
import time
import sys

class EntrExit(object):
    def __init__(self, unocup_num, clt_list, port, mode):
        self._unoccupyNum = unocup_num
        self.MAX_NUM = unocup_num
        self.port = port
        self._clt_list = list(clt_list)
        self._clt_list.remove(port)                                #其他节点
        self.wait_queue = Queue(maxsize = len(clt_list)-1)         #等待进入cs的节点
        self._in_going_cs = 0                                      #想要进入cs
        self._timestamp = 0.0
        self._in_cs = 0
        self.mode = mode
        self._exit = 0
        self.in_transaction = 0                                    #正在处理车辆进出
        self.transac_num = 0
        #开启tcp监听
        t = Thread(target=self.listen_ngb)
        t.setDaemon(True)
        t.start()
        Thread(target=self.deal_transaction).start()

    def terminate(self):
        self._exit = 1


    def deal_transaction(self):
        while not self._exit:
            if not self.in_transaction and self.transac_num > 0:
                Thread(target=self.operation).start()
                self.transac_num -= 1
                self.in_transaction = 1

    def operation(self):
        self.going_cs()
        self.get_cs()
        print "{0} 进入临界区....".format(self.port)
        self.car_opt()
        self.in_transaction = 0

    def get_cs(self):
        '''协商获取进入临界区的权限'''
        nghbors = []
        for port in self._clt_list:
            nghbors.append(Thread(target=self.request_cs, args=(port, self._timestamp,)))
        [cnn.start() for cnn in nghbors]
        [cnn.join() for cnn in nghbors]


    def listen_ngb(self):
        '''等待其他节点的连接'''
        sck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sck.bind(('127.0.0.1', self.port))
        sck.listen(5)
        conn_list = []
        while 1:
            conn, addr = sck.accept()
            conn_list.append(conn)
            Thread(target=self.deal_cnn, args=(conn,)).start()
        [cnn.close() for cnn in conn_list]
        sck.close()


    def deal_cnn(self, sck_cnn):
        '''处理来自其他节点的连接'''
        while 1 and not self._exit:
            data = sck_cnn.recv(1024).strip()
            if not data: break
            paras = data.split('#')
            if paras[0] == 'req':
                if self._in_going_cs == 0 and self._in_cs == 0:  #不在临界区也不想进
                    sck_cnn.sendall('ok')
                    break
                elif self._in_going_cs == 1:                    #想要进入临界区
                    peer_timestamp = paras[2]
                    if self._timestamp < peer_timestamp:
                        self.wait_queue.put(sck_cnn)
                    else:
                        sck_cnn.sendall('ok')
                        break
                else:                                           #本节点处于临界区
                    #print "{0} block {1}".format(self.port, sck_cnn)
                    self.wait_queue.put(sck_cnn)
            elif paras[0] == 'update':
                cmd = paras[1]
                if paras[1] == '+':
                    self._unoccupyNum += 1
                else:
                    self._unoccupyNum -= 1
                print '{0}:停车场空位数 {1}'.format(self.port, self._unoccupyNum)
                break
            elif paras[0] == 'car':                             #有车进入或驶出
                self.transac_num += 1
                break
        sck_cnn.close()


    def going_cs(self):
        '''想要进车或者出车'''
        self._in_going_cs = 1
        self._timestamp = '{0:.4f}'.format(time.time() + self.port / float(10000))
        print self.port, 'timestamp is ', self._timestamp
        time.sleep(1)


    def car_opt(self):
        '''停车场地*口操作'''
        self._in_going_cs = 0
        self._in_cs = 1

        if self.mode == 'in':
            if self._unoccupyNum == 0:
                print "停车场已满!!!"
            else:
                time.sleep(1)
                self._unoccupyNum -= 1
                # print '{0} send update msg to other'.format(self.port)
                self.snd_update(self.mode, self._clt_list)
        else:
            if self._unoccupyNum >= self.MAX_NUM:
                print "停车场没有车!!!"
            else:
                time.sleep(1)
                self._unoccupyNum += 1
                # print '{0} send update msg to other'.format(self.port)
                self.snd_update(self.mode, self._clt_list)

        self._in_cs = 0
        print '{0} 离开临界区...'.format(self.port)
        #给阻塞的节点发送同意消息
        while not self.wait_queue.empty():
            cnn = self.wait_queue.get()
            cnn.sendall('ok')
            cnn.close()


    @staticmethod
    def snd_update(mode, clt_list):
        '''给所有其他节点发消息更新停车位数目'''
        for port in clt_list:
            addr = ('127.0.0.1',port)
            client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            client.connect(addr)
            if mode == 'in':
                client.send('update#-')
            else:
                client.send('update#+')
            client.close()


    @staticmethod
    def request_cs(port, timestamp):
        addr = ('127.0.0.1',port)
        client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client.connect(addr)
        msg = 'req#{0}#{1}'.format(port, timestamp)
        while True:
            client.send(msg)
            data = client.recv(1024)
            if len(data) > 0:
                break
        client.close()

def send_req(port):
    addr = ('127.0.0.1',port)
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(addr)
    msg = 'car#opt'
    client.send(msg)
    client.close()

def main():
    entex = []
    port_list = [9801,9802,9803,9804,9805]
    a1 = EntrExit(2, port_list, 9801, 'in')         #入口
    entex.append(a1)
    a2 = EntrExit(2, port_list, 9802, 'in')
    entex.append(a2)
    a3 = EntrExit(2, port_list, 9803, 'in')
    entex.append(a3)
    a4 = EntrExit(2, port_list, 9804, 'out')        #出口
    entex.append(a4)
    a5 = EntrExit(2, port_list, 9805, 'out')
    entex.append(a5)

    send_req(9801)
    send_req(9801)
    send_req(9802)
    send_req(9803)
    send_req(9804)
    send_req(9805)
    return entex

if __name__ == '__main__':
    nodelist = main()
    time.sleep(10)
    [t.terminate() for t in nodelist]
