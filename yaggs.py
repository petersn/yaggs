#! /usr/bin/python

import struct, collections, socket

YAGGS_PORT = 50321

class Yaggs:
	def __init__(self, sock):
		self.sock = sock
		self.f = sock.makefile()
		self.queue = collections.deque()

	def get_string(self):
		length, = struct.unpack("<Q", self.f.read(8))
		return self.f.read(length)

	def put_strings(self, *strings):
		for s in strings:
			self.f.write(struct.pack("<Q", len(s)))
			self.f.write(s)
		self.f.flush()

	def enter(self, channel):
		"""enter(self, channel) -> joins a given channel"""
		self.f.write("E")
		self.put_strings(channel)

	def leave(self, channel):
		"""leave(self, channel) -> leaves a given channel"""
		self.f.write("L")
		self.put_strings(channel)

	def message(self, channel, message):
		"""message(self, channel, message) -> sends a message to a given channel"""
		self.f.write("M")
		self.put_strings(channel, message)

	def process(self, block=False):
		self.sock.setblocking(block)
		try:
			command = self.f.read(1)
			if command == "M":
				channel, message = self.get_string(), self.get_string()
				self.queue.appendleft((channel, message))
		except KeyboardInterrupt: pass
#		except (socket.timeout, socket.error):
#			pass

	@staticmethod
	def connect(address):
		sock = socket.create_connection((address, YAGGS_PORT))
		return Yaggs(sock)

