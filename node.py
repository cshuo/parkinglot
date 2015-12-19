#coding: utf-8
import socket
import os
import sys
from threading import Thread

def read_config(config_file):
    conf_dic = {}
    with open(config_file) as file_r:
        lines = file_r.readlines()

    ports = []
    for i in xrange(len(lines)):
        if i == 0:
            conf_dic['total'] = int(lines[i].strip())
        else:
            msg = lines[i].strip().split(',')
            ports.append((int(msg[0]), msg[1]))
    conf_dic['ports'] = ports
    return conf_dic

def send_req(port):
    addr = ('127.0.0.1',port)
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(addr)
    msg = 'car#opt'
    client.send(msg)
    client.close()

def main(conf):
    port_type = conf['ports']
    ports = [str(p[0]) for p in port_type]
    invailed = 0

    while 1:
        print_tips(conf)
        msg = raw_input('请输入进出口编号:')
        invailed = 0
        if not msg:
            continue
        else:
            paras = msg.split(',')
            for p in paras:
                if not p in ports:
                    invailed = 1
            if invailed:
                continue
            for p in paras:
                print 'send' + p
                port = int(p)
                send_req(port)

def print_tips(conf):
    total = conf['total']
    port_type = conf['ports']
    os.system('cls' if os.name == 'nt' else 'clear')
    print '----------------Attention-----------------'
    print '停车位共有{0}个'.format(total)
    for tp in port_type:
        if tp[1] == 'in':
            print '入口: {0}'.format(tp[0])
        else:
            print '出口: {0}'.format(tp[0])
    print '输入格式\n\t-单个进出操作: 9801\n\t-多个进出操作: 9801,9802,9804'
    print '----------------Ctrl-C 退出-----------------'

if __name__ == '__main__':
    try:
        conf = read_config('conf.txt')
        main(conf)
    except KeyboardInterrupt:
        sys.exit()
