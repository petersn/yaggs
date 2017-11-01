#! /usr/bin/python

import SocketServer, struct, threading

YAGGS_PORT = 50321

class YaggsServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
	allow_reuse_address = True

subscriptions = {}
key_value_store = {}
global_lock = threading.Lock()

class YaggsHandler(SocketServer.StreamRequestHandler):
	def handle(self):
		print "Connection from:", self.client_address[0]
		self.keep_going = True
		self.owned_variables = set()
		self.name = ""
		while self.keep_going:
			command = self.rfile.read(1)
			if not command:
				self.reap()
			if command == "E":
				# Enter a channel.
				channel_name = self.get_string()
				with global_lock:
					if channel_name not in subscriptions:
						subscriptions[channel_name] = set()
					subscriptions[channel_name].add(self)
			elif command == "L":
				# Leave a channel.
				channel_name = self.get_string()
				with global_lock:
					if channel_name in subscriptions and self in subscriptions[channel_name]:
						subscriptions[channel_name].remove(self)
			elif command == "M" or command == "T":
				echo = command == "M"
				# Send a message to a channel.
				channel_name = self.get_string()
				message = self.get_string()
				with global_lock:
					handler_list = list(subscriptions.get(channel_name, []))
					for handler in handler_list:
						# Don't echo for the "T" command.
						if handler == self and not echo:
							continue
						try:
							handler.wfile.write("M")
							handler.put_string(channel_name)
							handler.put_string(message)
						except:
							print "Error writing, reaping."
							handler.reap()
			elif command == "C":
				# Count number of people in a given channel.
				channel_name = self.get_string()
				with global_lock:
					names = [sub.name for sub in subscriptions.get(channel_name, [])]
					self.wfile.write("C" + struct.pack("<Q", len(names)))
					for name in names:
						self.put_string(name)
			elif command == "I":
				# Set my ID string.
				self.name = self.get_string()
			elif command == "N":
				# eNumerate all the channels.
				with global_lock:
					names = subscriptions.keys()
					self.wfile.write("N" + struct.pack("<Q", len(names)))
					for name in names:
						self.put_string(name)
			elif command == "S":
				# Set a key.
				key = self.get_string()
				value = self.get_string()
				with global_lock:
					key_value_store[key] = value
					# Take ownership of the key/value pair, so we can claim it when we reap.
					self.owned_variables.add(key)
			elif command == "G":
				# Get a key.
				key = self.get_string()
				print "REQUEST TO GET KEY:", key
				with global_lock:
					value = key_value_store.get(key, None)
					if value == None:
						print "ERROR!"
						self.wfile.write("E")
						self.put_string("key not found")
					else:
						print "Got response."
						self.wfile.write("S")
						self.put_string(key)
						self.put_string(value)
					print "done sending."
				print "done with key"

	def get_string(self):
		length = self.rfile.read(8)
		if len(length) != 8:
			self.reap()
		length, = struct.unpack("<Q", length)
		datum = self.rfile.read(length)
		if len(datum) != length:
			self.reap()
		return datum

	def put_string(self, s):
		self.wfile.write(struct.pack("<Q", len(s)))
		self.wfile.write(s)
		self.wfile.flush()

	def reap(self):
		global subscriptions
		self.keep_going = False
		with global_lock:
			# Remove ourself from the channels we're in.
			for handlers in subscriptions.values():
				if self in handlers:
					handlers.remove(self)
			# Get rid of our variables.
			for key in self.owned_variables:
				if key in key_value_store:
					key_value_store.pop(key)
			# Reduce the subscriptions to just the unempty ones.
			subscriptions = {k: v for k, v in subscriptions.iteritems() if v}

print "Running on port %s" % YAGGS_PORT
YaggsServer(("", YAGGS_PORT), YaggsHandler).serve_forever()

