from socket import *
import sys
import Image
import struct
import re
from threading import Thread
from time import sleep
from optparse import OptionParser

class BaseVNCServer(Thread):
    def __init__(self, conn, fbwidth=800, fbheight=600, name="goatvnc", image="gentoo.jpg"):
        self.conn = conn
        self.options = {'fbwidth':fbwidth, 'fbheight':fbheight, 'name':name, 'image':image}
        Thread.__init__(self)

    def run(self):
        self.handshake()
        self.initialize(**self.options)
        self.handle_requests()
        self.conn.close()

    def handshake(self, proto=(3,8)):
        """
        Step 1: Determining the version 
        """
        self.conn.send("RFB %03d.%03d\n" % proto)
        version_response = self.conn.recv(1024)
        m = re.search('RFB (\d\d\d)\.(\d\d\d)', version_response)
        if m:
            protos =  m.groups()
            """
            self.proto is a tuple of (major,minor) protocol version number
            """
            self.proto = (int(protos[0]), int(protos[1]))
        else:
            return
        """
        Step 2: Determining the security type
        """
        if self.proto in ((3, 7), (3, 8)):
            sec_types = struct.pack('!BB', 1, 1)
        elif self.proto in ((3,3)):
            sec_types = struct.pack('i', 1)
        self.conn.send(sec_types)
        sec_response = self.conn.recv(1024)
        self.sec_method =  struct.unpack('!B',sec_response)[0]
        if self.sec_method:
            self.conn.send(struct.pack('!i', 0))
        elif self.proto in ((3, 8)):
            print self.conn.recv()
            return
        else:
            return
        print "Connected success."

    def initialize(self,fbwidth,fbheight,name,image):
       shared = self.conn.recv(1024)
       #I don't know how to do this part
       pixel_format = struct.pack('!BBBBHHHBBBxxx',32,24,0,1,255,255,255,0,8,16)
       server_init = struct.pack('!HH',fbwidth,fbheight) + pixel_format + struct.pack('!I',len(name))+name
       self.conn.send(server_init)
       self.imgdata = Image.open(image).resize((800,600)).convert('RGBA').tostring()

    def handle_requests(self):
        self.first_fbupdate = True
        msg = ""
        while 1:
            msg += self.conn.recv(1024)
            if msg:
                #print "recv: %s" % (" ".join(["%x" %ord(x) for x in msg]))
                type = ord(msg[0])
                if type in range(8):
                    (self.do_SetPixel,0,self.do_SetEncodings,self.do_FramebufferUpdateRequest,self.do_KeyEvent,self.do_PointerEvent,self.do_ClientCutText)[type](msg)
                    msg = self.next_request(msg)
                else:
                    print "unknown request, noob"+type
            else:
                self.conn.close()

    def do_SetPixel(self,packet):
        pass

    def do_SetEncodings(self,packet):
        pass

    def do_FramebufferUpdateRequest(self,packet):
        #print struct.unpack('!BBHHHH',packet)
        print "sending shock site"
        self.conn.send(struct.pack('!BxH',0,1)+
                struct.pack('!HHHHi',0,0,800,600,0))
        self.conn.send(self.imgdata)
        # ghetto rate limiting
        sleep(1)

    def do_KeyEvent(self,packet):
        pass

    def do_PointerEvent(self,packet):
        print "pointer event!"

    def do_ClientCutText(self,packet):
        pass

    def next_request(self,packet):
        type = ord(packet[0])
        if type == 2:
            length = struct.unpack('!xxH', packet[:4])[0]
        elif type == 6:
            length = struct.unpack('!4xI', packet[:8])[0]
        else:
            length = 0
        length = [20, 0, 4+4*length, 10, 8, 6, 8+length]
        return packet[length[type]:]


class VNCDispatcher(object):
    def __init__(self, host='', port=5900, handler=BaseVNCServer, args=None):
        args = args or {}
        self.s =  socket(AF_INET,SOCK_STREAM)
        self.s.bind((host, port))
        self.s.listen(1)
        while 1:
            conn, addr = self.s.accept()
            print 'Connection from: ',addr
            h = handler(conn=conn, **args)
            h.start()

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-p", "--port", dest="port", type="int", help="TCP port to listen on", default=5900)
    parser.add_option("-i", "--image",dest="image", help="Image to serve", default="gentoo.jpg")
    (options, args) = parser.parse_args()
    b = VNCDispatcher(port=options.port, args={'image':options.image})
