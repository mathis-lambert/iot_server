import json
import logging
import socketserver
import threading
from typing import Any, Dict, Callable, Optional

from pydantic import BaseModel, ValidationError

from .classes.serial_uart import serial_uart
from .database.mongodb import mongo_client
from .settings import settings


class UDPMessage(BaseModel):
    request: str
    data: Dict[str, Any]


"""
{
    "request": "ping",
    "data": {}
}
"""


def parse_udp_message(raw: bytes) -> Optional[UDPMessage]:
    """Renvoie un UDPMessage valide ou None si parsing / validation échoue."""
    try:
        # check if begin with {
        if not raw.startswith(b"{"):
            raise ValueError("Invalid JSON")

        payload = json.loads(raw.decode("utf-8"))
        return UDPMessage(**payload)
    except (json.JSONDecodeError, ValidationError, ValueError) as exc:
        logging.warning("Message invalide : %s - %s", raw, exc)
        return None


def _handle_ping(msg: UDPMessage) -> str:
    return "pong"


def _handle_get_values(msg: UDPMessage) -> str:
    logging.info("get-values: %s", msg.data)
    device_id = msg.data.get("device_id", "")

    if not device_id:
        return "err: missing device_id"

    # Récupération du dernier document pour le deviceId, timestamp le plus récent
    value = mongo_client.find(
        {"deviceId": device_id},
        limit=1,
        sort=[("timestamp", -1)],
        filter={"value": 1, "_id": 0},
    )

    if not value:
        return "err: no data found"

    resp = value[0].get("value", {})

    return json.dumps(resp)  # Renvoie la liste des derniers documents


def _handle_update_screen(msg: UDPMessage) -> str:
    """Met à jour l'écran LCD avec les valeurs fournies."""
    data = msg.data
    logging.info("update-screen: %s", data)
    device_id: str = data.get("device_id", "")
    order: str = data.get("sensor_order", "")

    if not device_id or not order:
        return "Error sending ctrl packet"

    packet: bytes = f"SETORDER,{device_id.split("device-00")[-1]},{''.join(order)}".encode("utf-8")
    serial_uart.send_message(packet)
    logging.info("Commande envoyée au µC : %s", packet)
    return "ack"


def _handle_get_devices(msg: UDPMessage) -> str:
    pipeline = [
        {
            "$match": {
                "deviceId": {"$regex": r"^device-00[1-9]$"},
                "timestamp": {"$exists": True},
            }
        },
        {
            "$group": {"_id": "$deviceId"}
        },
        {
            "$sort": {"_id": 1}
        }
    ]

    result = mongo_client.aggregate(pipeline)
    devices_list = [doc["_id"] for doc in result]

    if not devices_list:
        return json.dumps({"error": "no devices found"})

    return json.dumps(devices_list)


ROUTES: dict[str, Callable[[UDPMessage], str]] = {
    "ping": _handle_ping,
    "get-values": _handle_get_values,
    "update-screen": _handle_update_screen,
    "get-devices": _handle_get_devices,
}


def dispatch(msg: UDPMessage) -> str:
    """Trouve le handler adapté ou renvoie une erreur."""
    handler = ROUTES.get(msg.request)
    if handler:
        return handler(msg)
    return "err: unknown request"


class ThreadedUDPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:  # type: ignore[override]
        raw_data: bytes = self.request[0].strip()
        sock = self.request[1]

        if not raw_data:
            sock.sendto(b"err: empty payload", self.client_address)
            return

        msg = parse_udp_message(raw_data)
        if not msg:
            sock.sendto(b"err: invalid json", self.client_address)
            return

        reply = dispatch(msg)
        sock.sendto(reply.encode("utf-8"), self.client_address)

        # Log minimal mais lisible
        logging.info(
            "%s: %s ➜ %s",
            threading.current_thread().name,
            self.client_address,
            msg.request,
        )


class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    daemon_threads = True  # coupe proprement à la fermeture du process
    allow_reuse_address = True


def run(host: str = settings.server_host, port: int = settings.server_port) -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-8s | %(message)s",
    )
    with ThreadedUDPServer((host, port), ThreadedUDPRequestHandler) as server:
        logging.info("Serveur UDP prêt sur %s:%s", host, port)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logging.info("Arrêt demandé (Ctrl-C) – bye !")
