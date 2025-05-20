import socketserver
import threading

from .serial_uart import serial_uart

MICRO_COMMANDS = [b'TL', b'LT']


class ThreadedUDPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data: bytes = self.request[0].strip()
        socket = self.request[1]
        current_thread = threading.current_thread()
        print(f"{current_thread.name}: client: {self.client_address}, wrote: {data}")

        if not data:
            print("No data received")
            return

        if data in MICRO_COMMANDS:  # Send message through UART
            serial_uart.send_message(data)
            socket.sendto(b'OK', self.client_address)

        elif data == b'getValues()':  # Sent last value received from micro-controller
            print("Sending last value received from micro-controller")
            # socket.sendto(LAST_VALUE.encode("utf-8"), self.client_address)
            # TODO: Create last_values_received with mongodb
        else:
            print("Unknown message: ", data)


class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    pass
