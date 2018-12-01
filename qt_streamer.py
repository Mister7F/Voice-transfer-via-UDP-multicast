import sys
import socket
import struct
from threading import Thread
from PyQt5.QtMultimedia import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from Crypto.Cipher import AES


key = b'0' * 16
encryptor = AES.new(key, AES.MODE_ECB)

app = QApplication(sys.argv)

FORMAT = QAudioFormat()
FORMAT.setSampleRate(44100)
FORMAT.setChannelCount(1)
FORMAT.setSampleSize(32)
FORMAT.setSampleType(QAudioFormat.SignedInt);
FORMAT.setByteOrder(QAudioFormat.LittleEndian);
FORMAT.setCodec("audio/pcm")

MULTICAST_IP = '224.3.29.71'
PORT = 9999

def pad(data):
    if not len(data):
        return data

    missing_size = 16 - len(data) % 16
    data += bytes([missing_size] * missing_size)
    return data

def unpad(data):
    if not len(data):
        return data

    missing_size = data[-1]

    if missing_size > 16:
        return data

    return data[:missing_size]

class Sender():
    def __init__(self):
        self._input = QAudioInput(FORMAT)
        self._input_device = self._input.start()
        self._input_device.readyRead.connect(self._stream_callback)

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)


    def _stream_callback(self):
        global encryptor
        data = self._input_device.readAll()

        data = encryptor.encrypt(pad(data.data()))

        self._sock.sendto(data, (MULTICAST_IP, PORT))


class Player(Thread):
    def __init__(self):
        Thread.__init__(self)
        self._output = QAudioOutput(FORMAT)
        self._output_device = self._output.start()


        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self._sock.bind(('0.0.0.0', PORT))
        group = socket.inet_aton(MULTICAST_IP)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self.stop = False

    def run(self):
        print(socket.gethostname())
        while not self.stop:
            global encryptor
            data, (client_ip, src_port) = self._sock.recvfrom(65535)

            data = unpad(encryptor.decrypt(data))
            print(len(data))
            self._output_device.write(data)

sender = Sender()
player = Player()
player.start()


app.exec_()

player.stop = True
player.join()
