import platform    # For getting the operating system name
import subprocess  # For executing a shell command
import socket

from serial.tools.list_ports import comports

from .main_window_gui import Ui_MainWindow

from PyQt6.QtWidgets import QMainWindow
from PyQt6.QtCore import pyqtSlot, QThread, pyqtSignal

from ctypes import LittleEndianStructure, c_uint32, c_uint16, c_uint8
from serial import Serial
from typing import Union


class WorkerThread(QThread):
    finished_signal = pyqtSignal()

    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self._stop = False

    @property
    def stop(self):
        return self._stop

    @stop.setter
    def stop(self, value):
        self._stop = value

    def run(self):
        while not self.stop:
            self.callback()
        self.finished_signal.emit()


def generate_packet(payload: bytes, baudrate: int) -> LittleEndianStructure:
    class Packet(LittleEndianStructure):
        _pack_ = 1
        _fields_ = (
            ("signature", c_uint16),
            ("payload_length", c_uint16),
            ("baudrate", c_uint32),
            ("payload", c_uint8 * len(payload)),
            ("crc", c_uint16)
        )
    obj = Packet()
    obj.signature = 0xb562
    obj.payload_length = len(bytes)
    obj.baudrate = baudrate
    obj.payload = payload

    return obj


class MainWindow(Ui_MainWindow, QMainWindow):

    def __init__(self, debug: bool = False):
        super().__init__()
        self.setupUi(self)
        self.debug = debug
        self.ser: Union[None, Serial] = None
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.socket.bind("0.0.0.0")
        self.connection_thread = None
        for port, desc, hwid in comports():
            self.rc.addItem(port)

    def connection_handler(self):
        ip = self.ip_addr.text()
        data = self.ser.readline()
        if self.debug:
            print(data)
        packet = generate_packet(data, len(data))
        self.socket.sendto(packet, (ip, 9000))

    @pyqtSlot()
    def on_ping_btn_clicked(self):
        """
            Returns True if host (str) responds to a ping request.
            Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
            """

        # Option for the number of packets as a function of
        param = '-n' if platform.system().lower() == 'windows' else '-c'

        # Building the command. Ex: "ping -c 1 google.com"
        command = ['ping', param, '1', self.ip_addr.text()]

        res = subprocess.call(command)
        if res == 0:
            self.statusbar.showMessage("Ping succeeded")
        else:
            self.statusbar.showMessage("Ping failed")

    @pyqtSlot()
    def on_remote_btn_clicked(self):
        if self.remote_btn.text().lower() == "disconnect remote":
            self.connection_thread.stop = True
            self.remote_btn.setText("Connect remote")
        else:
            self.connection_thread = WorkerThread(self.connection_handler)
            self.remote_btn.setText("Disconnect remote")
            self.connection_thread.start()

    @pyqtSlot()
    def on_connect_btn_clicked(self):
        dev = self.rc.currentText()
        bd = self.baudrate.currentText()
        if bd.lower() == 'unknown':
            return
        self.ser = Serial(port=dev, baudrate=int(bd))
