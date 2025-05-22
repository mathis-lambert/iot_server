import json
import logging
import random
import threading
from datetime import datetime, UTC
from time import sleep

from pydantic import BaseModel, ValidationError

from iot_server.classes.serial_uart import SerialUART
from iot_server.database.mongodb import mongo_client
from iot_server.settings import settings
from iot_server.udp_handler import run as run_udp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)


class SensorData(BaseModel):
    id: int
    t: float
    h: float
    p: float
    lux: float


class App:
    FILENAME = "./data/values.txt"

    def __init__(self) -> None:
        # --- infra --------------------------------------------------------- #
        self.serial_uart = SerialUART()
        self.serial_uart.init_uart()

        # fichier de log des valeurs
        self.file = open(self.FILENAME, "a", buffering=1)

        # démarrage du serveur UDP dans un thread
        self.udp_thread = threading.Thread(
            target=run_udp,
            name="udp-server",
            daemon=True,
            kwargs=dict(host=settings.server_host, port=settings.server_port),
        )
        self.udp_thread.start()

        self._stop = threading.Event()

    def _simulate_sensors(self) -> None:
        """Pseudo-capteurs → MongoDB toutes les 5 s."""
        while not self._stop.is_set():
            doc = {
                "deviceId": "device-001",
                "timestamp": datetime.now(UTC),
                "value": {
                    "t": round(random.uniform(20.0, 30.0), 1),
                    "h": round(random.uniform(40.0, 85.0), 1),
                    "p": round(random.uniform(980, 1030), 0),
                },
            }
            mongo_client.insert_one(doc)
            logging.debug(f"Document inserted : {doc}")
            sleep(5)

    def _read_serial(self) -> None:
        """Lecture UART en continu → fichier + MongoDB."""
        while not self._stop.is_set() and self.serial_uart.ser.isOpen():
            line = self.serial_uart.ser.readline()
            if line:
                msg = line.decode().rstrip()
                self.file.write(msg + "\n")
                logging.info(f"Message <{msg}> received from micro-controller.")

                try:
                    data_dict = json.loads(msg)
                    sensor_data = SensorData(**data_dict)  # Validation automatique ici
                    doc = {
                        "deviceId": f"device-00{sensor_data.id}",
                        "timestamp": datetime.now(UTC),
                        "value": {
                            "t": sensor_data.t,
                            "h": sensor_data.h,
                            "p": sensor_data.p,
                            "lux": sensor_data.lux,
                        }
                    }
                    mongo_client.insert_one(doc)
                except (json.JSONDecodeError, ValidationError) as e:
                    logging.debug(f"Erreur de parsing ou validation : {e}")

    def run(self) -> None:
        sensor_thread = threading.Thread(
            target=self._simulate_sensors, name="sensor-sim", daemon=True
        )
        serial_thread = threading.Thread(
            target=self._read_serial, name="serial-read", daemon=True
        )

        # sensor_thread.start()
        serial_thread.start()

        logging.debug(
            f"UDP server listening on {settings.server_host}:{settings.server_port}  "
            "(threads sensor-sim / serial-read démarrés)"
        )

        try:
            # boucle d’attente active : ^C interrompt le process
            while True:
                sleep(1)
        except (KeyboardInterrupt, SystemExit):
            logging.debug("Stopping…")
            self._stop.set()
            sensor_thread.join()
            serial_thread.join()
            self.file.close()
            self.serial_uart.ser.close()
            logging.debug("Bye !")


if __name__ == "__main__":
    App().run()
