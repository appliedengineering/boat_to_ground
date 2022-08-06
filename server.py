import pickle

from twisted.internet.protocol import Protocol, Factory
from twisted.internet import reactor

class Server(Protocol):
    """
    Rendezvous server
    New object is initialized for every connection
    """
        
    def connectionLost(self, reason) -> None:
        if self.transport.client in self.factory.clients:
            del self.factory.clients[self.transport.client]

        if self.transport.client in self.factory.addresses:
            del self.factory.addresses[self.transport.client]

        # broadcast removal
        for key in self.factory.clients:
            self.factory.clients[key].transport.write(pickle.dumps(self.transport.client))

    def dataReceived(self, data) -> None:
        # server is going to receive some data
        data = pickle.loads(data)
        
        for key in self.factory.clients:
            # where key is the address
            self.factory.clients[key].transport.write(pickle.dumps([self.transport.client, data]))
        
        if self.factory.addresses:
            self.transport.write(pickle.dumps(self.factory.addresses))
            # initialize the list of addresses for new client

        self.factory.addresses[self.transport.client] = data
        # data is a list of their listeners
        self.factory.clients[self.transport.client] = self


