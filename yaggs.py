#! /usr/bin/python
"""
Yaggs client implementation.

To make a Yaggs connection, either pass in a socket:

	import socket
	sock = socket.create_connection((host, port))
	y = Yaggs(sock)

Or, equivalently, with an optional port that defaults to 50321:

	y = Yaggs.connect(host, port=...)

Now, let's send a message to ourself:

	y.enter("some_room")
	y.message("some_room", "Hello, there!")
	y.process(block=True)
	print y.queue.pop()
	y.close()

The queue used for y.queue is collections.deque, which is thread safe.
This lets us spawn off a thread to manage the processing, if we want:

	import thread
	def process(y):
		while True:
			y.process(block=True)
	thread.start_new_thread(process, (y,))
	# Now y.queue fills up magically, all by itself!
"""

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
		"""process(self) -> reads messages from the network, and saves them to self.queue"""
		self.sock.setblocking(block)
		try:
			command = self.f.read(1)
			if command == "M":
				channel, message = self.get_string(), self.get_string()
				self.queue.appendleft((channel, message))
		except socket.timeout:
			pass

	def close(self):
		self.sock.close()

	@staticmethod
	def connect(address, port=None):
		"""connect(self, address, port=50321) -> calls socket.create_connection, then wraps with Yaggs()"""
		sock = socket.create_connection((address, (YAGGS_PORT if port is None else port)))
		return Yaggs(sock)

