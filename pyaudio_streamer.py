import pyaudio
import socket
import struct
from threading import Thread


MULTICAST_IP = '224.3.29.71'
PORT = 8521


class Sender():
    def __init__(self):
        self._stream = pyaudio.PyAudio().open(format=pyaudio.paInt16,
                                              channels=1, rate=44100,
                                              input=True, frames_per_buffer=1024,
                                              stream_callback=self._stream_callback)

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 32)

    def start_recording(self):
        self._stream.start_stream()

    def _stream_callback(self, in_data, frame_count, time_info, status):

        self._sock.sendto(in_data, (MULTICAST_IP, PORT))

        return (None, pyaudio.paContinue)

    def stop(self):
        self._stream.stop_stream()
        self._stream.close()


class Player(Thread):
    def __init__(self):
        Thread.__init__(self)
        self._player = pyaudio.PyAudio().open(format=pyaudio.paInt16,
                                              channels=1, rate=44100,
                                              output=True, frames_per_buffer=1024)

        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self._sock.bind(('0.0.0.0', PORT))
        group = socket.inet_aton(MULTICAST_IP)
        mreq = struct.pack('4sL', group, socket.INADDR_ANY)
        self._sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        self.stop = False

    def run(self):
        print(socket.gethostname())
        while not self.stop:
            enc_data, (client_ip, src_port) = self._sock.recvfrom(2048)
            self._player.write(enc_data)


sender = Sender()

player = Player()

player.start()


while not player.stop:
    r = input('''0: Exit \r\n''')
    player.stop = r == '0'



print('Wait to clean...')
player.join()
sender.stop()
