import socket
import client
import server

from twisted.internet import reactor


i = input("host or join?")

if i == "host":
    port = client.get_free_ports(1)[0]
    print(f"Hosting on {(socket.gethostbyname(socket.gethostname()), port)}")
    server_factory = server.Factory()
    server_factory.protocol = server.Server
    server_factory.clients = {}
    server_factory.addresses = {} 

    reactor.listenTCP(port, server_factory)

    # client_factory = client.ClientFactory()

    # reactor.connectTCP(socket.gethostbyname(socket.gethostname()), port, client_factory)
    
else:
    ip, port = input("IP "), int(input("Port "))
    client_factory = client.ClientFactory()
    
    reactor.connectTCP(ip, port, client_factory)

    reactor.listenUDP(client.ports[0], client.AudioProtocol(client_factory))
    reactor.listenUDP(client.ports[1], client.MessageProtocol(client_factory))

reactor.run()