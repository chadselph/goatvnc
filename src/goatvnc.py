import Image
import struct
from time import sleep


from twisted.internet import reactor
from twisted.internet.protocol import Protocol, Factory


class RFBServer(Protocol):
    "Protocol for Remote Frame Buffer"
    def __init__(self, fbwidth=800, fbheight=600, name="goatvnc", version=(3, 8)):

        self.step = self.handshake
        self.buff = []
        self.options = {
            'fbwidth': fbwidth,
            'version': version,
        }

    def connectionMade(self):
        self.transport.write("RFB 003.008\n")

    def dataReceived(self, data):
        print data
        self.step(data)

    def handshake(self, data):
        """
        Step 1: Determining the version 
        """
        if data[:3] == "RFB":
            major,minor = [int(x) for x in data[4:].split('.')]
            self.version = (major, minor)
        else:
            return
        """
        Step 2: Determining the security type
        """
        if self.version in ((3,7),(3,8)):
            sec_types = struct.pack('!BB',1,1)
        elif self.version in ((3,3)):
            sec_types = struct.pack('i',1)
        self.transport.write(sec_types)
        self.step = self.set_security


    def set_security(self, data):
        sec_response = data
        self.sec_method =  struct.unpack('!B',sec_response)[0]
        if self.sec_method:
            self.transport.write(struct.pack('!i',0))
        elif self.version in ((3,8)):
            return
        else:
            return
        self.step = self.initialize


    def initialize(self, data):
        #I don't know how to do this part
        pixel_format = struct.pack('!BBBBHHHBBBxxx',32,24,0,1,255,255,255,0,8,16)
        server_init = struct.pack('!HH',self.options['fbwidth'],self.options['fbheight']) + pixel_format + struct.pack('!I',len(name))+name
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
            length = struct.unpack('!xxH',packet[:4])[0]
        elif type == 6:
            length = struct.unpack('!4xI',packet[:8])[0]
        else:
            length = 0
        length = [20,0,4+4*length,10,8,6,8+length]
        return packet[length[type]:]

"""
class VNCDispatcher(object):
    def __init__(self,host='',port=5900,handler=BaseVNCServer,args={}):
        self.s =  socket(AF_INET,SOCK_STREAM)
        self.s.bind((host,port))
        self.s.listen(1)
        while 1:
            conn, addr = self.s.accept()
            print 'Connection from: ',addr
            h = handler(conn=conn,**args)
            h.start()
            """

if __name__ == "__main__":
    """
    parser = OptionParser()
    parser.add_option("-p","--port",dest="port",type="int",help="TCP port to listen on")
    parser.add_option("-i","--image",dest="image",help="Image to serve")
    (options,args) = parser.parse_args()
    port = options.port or 5900
    image = options.image or "gentoo.jpg"
    b = VNCDispatcher(port=port,args={'image':image})
    """

    factory = Factory()
    factory.protocol = RFBServer
    reactor.listenTCP(5900, factory)
    reactor.run()
