# udp_server.py
import json
import logging
import socketserver
import threading
from typing import Any, Dict, Callable, Optional

from pydantic import BaseModel, ValidationError

from .serial_uart import serial_uart   # ton module existant

# --------------------------------------------------------------------------- #
# 1. Modèle Pydantic : garantit qu’on reçoit bien {"request": str, "data": {}} #
# --------------------------------------------------------------------------- #

class UDPMessage(BaseModel):
    request: str
    data: Dict[str, Any]

# --------------------------------------------------------------------------- #
# 2. Parsing + validation                                                     #
# --------------------------------------------------------------------------- #

def parse_udp_message(raw: bytes) -> Optional[UDPMessage]:
    """Renvoie un UDPMessage valide ou None si parsing / validation échoue."""
    try:
        payload = json.loads(raw.decode("utf-8"))
        return UDPMessage(**payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        logging.warning("Message invalide : %s", exc)
        return None

# --------------------------------------------------------------------------- #
# 3. Routage : un dict « request » ➜ fonction                                 #
# --------------------------------------------------------------------------- #

def _handle_ping(msg: UDPMessage) -> str:
    return "pong"

def _handle_command(msg: UDPMessage) -> str:
    # Ex. le smartphone envoie {"request":"command", "data":{"value":"LED_ON"}}
    value = msg.data.get("value", "")
    serial_uart.send_message(value.encode("utf-8"))
    logging.info("Commande envoyée au µC : %s", value)
    return "ack"

ROUTES: dict[str, Callable[[UDPMessage], str]] = {
    "ping": _handle_ping,
    "command": _handle_command,
    # ajoute d’autres handlers ici…
}

def dispatch(msg: UDPMessage) -> str:
    """Trouve le handler adapté ou renvoie une erreur."""
    handler = ROUTES.get(msg.request)
    if handler:
        return handler(msg)
    return "err: unknown request"

# --------------------------------------------------------------------------- #
# 4. Handler UDP threaded                                                     #
# --------------------------------------------------------------------------- #

class ThreadedUDPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:                              # type: ignore[override]
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
        logging.debug(
            "%s: %s ➜ %s",
            threading.current_thread().name,
            self.client_address,
            msg.request,
        )

# --------------------------------------------------------------------------- #
# 5. Serveur                                                                 #
# --------------------------------------------------------------------------- #
class ThreadedUDPServer(socketserver.ThreadingMixIn, socketserver.UDPServer):
    daemon_threads = True          # coupe proprement à la fermeture du process
    allow_reuse_address = True

def run(host: str = "0.0.0.0", port: int = 10000) -> None:
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
