import os

import serial
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class SerialUART:
    # send a serial message
    SERIAL_PORT = os.getenv("PERIPHERAL_PORT", "/dev/tty.usbmodem1102")
    BAUDRATE = os.getenv("PERIPHERAL_BAUDRATE", 115200)
    ser = serial.Serial()

    def init_uart(self):
        # ser = serial.Serial(SERIAL_PORT, BAUDRATE)
        self.ser.port = self.SERIAL_PORT
        self.ser.baudrate = self.BAUDRATE
        self.ser.bytesize = serial.EIGHTBITS  # number of bits per bytes
        self.ser.parity = serial.PARITY_NONE  # set parity check: no parity
        self.ser.stopbits = serial.STOPBITS_ONE  # number of stop bits
        self.ser.timeout = None  # block read

        # self.ser.timeout = 0 #non-block read
        # self.ser.timeout = 2 #timeout block read
        self.ser.xonxoff = False  # disable software flow control
        self.ser.rtscts = False  # disable hardware (RTS/CTS) flow control
        self.ser.dsrdtr = False  # disable hardware (DSR/DTR) flow control
        # self.ser.writeTimeout = 0 #timeout for write

        print("Starting Up Serial Monitor")
        try:
            self.ser.open()
        except serial.SerialException:
            print("Serial {} port not available".format(self.SERIAL_PORT))
            exit()

    def send_message(self, msg: bytes):
        self.ser.write(msg + b"\n")  # \n is needed to signal the end of the message
        self.ser.flush()
        print(f"Message <{msg.decode()}> sent to micro-controller.")


serial_uart = SerialUART()
