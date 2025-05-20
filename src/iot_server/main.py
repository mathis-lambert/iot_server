# Program to control passerelle between Android application
# and micro-controller through USB tty
import random
import threading
from datetime import datetime, UTC
from time import sleep

from classes import (
    SerialUART,
    ThreadedUDPServer,
    ThreadedUDPRequestHandler
)
from database import MongoDB
from settings import settings


class App:
    HOST = "0.0.0.0"
    UDP_PORT = 10000
    FILENAME = "./data/values.txt"
    LAST_VALUE = ""

    def __init__(self):
        self.mongo_client = MongoDB(
            settings.mongo_host,
            settings.mongo_port,
            settings.mongo_username,
            settings.mongo_password,
            "iot",
            "events"
        )

        self.serial_uart = SerialUART()
        self.serial_uart.init_uart()

        self.udp_server = ThreadedUDPServer((self.HOST, self.UDP_PORT), ThreadedUDPRequestHandler)

        self.file = open(self.FILENAME, "a")

        self.server_thread = threading.Thread(target=self.udp_server.serve_forever)
        self.server_thread.daemon = True

    def handle(self):
        try:
            self.server_thread.start()
            print(f"Server started at {self.HOST} port {self.UDP_PORT}")

            while True:
                # Exemple de deviceId (tu peux adapter si tu as plusieurs devices)
                device_id = "device-001"

                # Génération aléatoire des mesures
                temperature = round(random.uniform(20.0, 30.0), 1)  # t entre 20.0 et 30.0 °C
                humidity = round(random.uniform(40.0, 85.0), 1)  # h entre 40 et 85 %
                pressure = round(random.uniform(980, 1030), 0)  # p entre 980 et 1030 hPa

                doc = {
                    "deviceId": device_id,
                    "timestamp": datetime.now(UTC),
                    "value": {
                        "t": temperature,
                        "h": humidity,
                        "p": pressure
                    }
                }

                self.mongo_client.insert_one(doc)
                print(f"Document inserted : {doc}")
                sleep(5)

            while self.serial_uart.ser.isOpen():
                line = self.serial_uart.ser.readline()  # bloque jusqu’à '\n' ou timeout
                if line:  # si non vide
                    msg = line.decode().rstrip()  # enlève '\r\n'
                    self.file.write(msg + "\n")
                    self.mongo_client.insert_one({"value": msg})
                    print("Message <" + msg + "> received from micro-controller.")

        except (KeyboardInterrupt, SystemExit):
            print("Stopping server...")
            self.udp_server.shutdown()
            self.udp_server.server_close()
            self.file.close()
            self.serial_uart.ser.close()
            print("Server stopped. Closing...")
            exit()


# Main program logic follows:
if __name__ == '__main__':
    app = App()
    app.handle()
