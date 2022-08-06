import sys
import pickle
import pyaudio
import socket 

from twisted.internet.protocol import DatagramProtocol, Protocol, ClientFactory as CFactory
from twisted.internet import reactor

def get_free_ports(N):
    ports = []
    for i in range(N):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("0.0.0.0", 0))
        port = sock.getsockname()[1]
        sock.close()
        ports.append(port)
    return ports

ports = get_free_ports(2) 
# first port is audio
# second is for messaging

class Client(Protocol):
    def connectionMade(self):
        self.transport.write(pickle.dumps(ports))

    def dataReceived(self, data):
        data = pickle.loads(data)
        if isinstance(data, dict):
            # init
            print(f"Initialize {data}")
            for key in data:
                self.factory.audio[key] = (key[0], data[key][0])
                self.factory.message[key] = (key[0], data[key][1])

        elif isinstance(data, list):
            # append
            print(f"Append {data}")
            self.factory.audio[data[0]] = (data[0][0], data[1][0])
            self.factory.message[data[0]] = (data[0][0], data[1][1])

        elif isinstance(data, tuple):
            # removal
            print(f"Remove {data}")
            del self.factory.audio[data]   
            del self.factory.message[data]   
        
class ClientFactory(CFactory):
    audio = {}
    message = {}
    protocol = Client
    
    
    def clientConnectionFailed(self, connector, reason):
       reactor.stop()
    
    def clientConnectionLost(self, connector, reason):
       reactor.stop() 


class AudioProtocol(DatagramProtocol):
    def __init__(self, factory) -> None:
        self.factory = factory

    def startProtocol(self):
        __pyaudio_obj = pyaudio.PyAudio()
        self.buffer = 1024 
        
        self.output_stream = __pyaudio_obj.open(format=pyaudio.paInt16,
                                           output=True, rate=44100, channels=1,
                                           frames_per_buffer=self.buffer)
        self.input_stream = __pyaudio_obj.open(format=pyaudio.paInt16,
                                          input=True, rate=44100, channels=1,
                                          frames_per_buffer=self.buffer)
        
        reactor.callInThread(self.record)

    def record(self):
        while True:
            data = self.input_stream.read(self.buffer)
            self.broadcast(data)

    def broadcast(self, data):
        if self.factory.audio:
            for key in self.factory.audio:
                try:
                    self.transport.write(data, self.factory.audio[key])
                except Exception as e: # client dced
                    pass

    def datagramReceived(self, datagram, addr):
        self.output_stream.write(datagram)


class MessageProtocol(DatagramProtocol):
    def __init__(self, factory) -> None:
        self.factory = factory

    def startProtocol(self):
        reactor.callInThread(self.listen)

    def listen(self):
        while True:
            i = input(">")
            self.broadcast(i.encode(encoding="UTF-8"))

    def broadcast(self, data):
        if self.factory.message:
            for key in self.factory.message:
                try:
                    self.transport.write(data, self.factory.message[key])
                except Exception as e: # client dced
                    pass

    def datagramReceived(self, datagram, addr):
        print(f"{addr} - {datagram.decode(encoding='UTF-8')}")