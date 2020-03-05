import socket
from threading import Thread, Lock
from json import dumps as dictToJson
from json import loads as jsonToDict
from json.decoder import JSONDecodeError
from common import encodeImg

#################
### CONSTANTS ###
#################

from constants import ACK, NEWLINE, IMG_MSG_S, IMG_MSG_E
from constants import ADDR, PORT, TIMEOUT, SIZE

####################
### CLIENT CLASS ###
####################

class client:
	def __init__(self, addr='127.0.0.1', timeout=TIMEOUT, port=8080, size=SIZE, open=True):
		self.addr = addr
		self.port = port
		self.canWrite = True
		self.channels = {}
		self.timeout = timeout
		self.size = size
		self.lock = Lock()
		self.opened = False
		self.stopped = False
		if open:
			self.open()

	def set_timeout(self, time):
		self.timeout = time

	def open(self):
		while True:
			try:
				self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
				self.socket.settimeout(self.timeout)
				self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
				self.socket.connect((self.addr, self.port))
				break
			except OSError as e:
				if type(e) is ConnectionRefusedError:
					continue
				raise RuntimeError("Socket address in use: {}".format(e))
				return
			except socket.timeout:
				continue
		self.opened = True

	def start(self):
		Thread(target=self.run, args=()).start()
		return self

	def run(self):
		tmp = ''
		while True:
			if self.stopped:
				self.socket.close()
				return

			try:
				tmp += self.socket.recv(self.size).decode()
				msg = jsonToDict(tmp)
				self.channels[msg['type']] = msg['data']
				if(msg['type'] == ACK):
					self.canWrite = True
				tmp = ''
			except JSONDecodeError: 
				continue
			except socket.timeout:
				continue
			except OSError:
				self.close()

	def get(self, channel):
		if channel in self.channels.keys():
			return self.channels[channel]
		return None

	def writeLock(self, channel, data):
		with self.lock:
			self.write(channel, data)

	def write(self, channel, data):
		if self.canWrite:
			self.canWrite = False
			msg = {'type': channel, 'data': data}
			self.socket.sendall(dictToJson(msg).encode() + NEWLINE)

	def writeImgLock(self, data):
		with self.lock:
			self.writeImg(data)

	def writeImg(self, data):
		if self.canWrite:
			self.canWrite = False
			msg = IMG_MSG_S + encodeImg(data) + IMG_MSG_E
			self.socket.sendall(msg + NEWLINE)

	def close(self):
		self.opened = False
		self.stopped = True
