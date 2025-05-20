import socket
import sys

HOST, PORT = "localhost", 10000
data = " ".join(sys.argv[1:]).encode("utf-8")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

sock.sendto(data, (HOST, PORT))
received = sock.recv(1024)

print("Sent:     {}".format(data))
print("Received: {}".format(received))
