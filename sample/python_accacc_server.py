# -*- coding: utf-8 -*-
# python2 accacc PC server sample

import socket
import struct
import datetime
import time
import threading

class ServerThread(threading.Thread):
	def __init__(self, host, port):
		threading.Thread.__init__(self)

		self.host = host
		self.port = port
		self.conn = None
		self.flag_stop = False

		# millisec
		self.time_last_pon = time.time() * 1000
		self.count_pon = 0

	def get_data(self, conn):
		size_float = 4
		size_data = 6 * size_float
		data = ()
		d = conn.recv(size_data)
		if len(d) < size_data:
			return ()
		# 24byte binary -> bigendian(float, float, float, float, float, float)
		data = struct.unpack(">6f", d)
		return  data

	def run(self):
		# server socket
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		sock.setblocking(0)
		sock.bind((self.host, self.port))
		sock.listen(1)

		print("start server accept loop")
		self.conn = None
		while self.flag_stop is False:
			try:
				self.conn, addr = sock.accept()
			except Exception as e:
				continue
			if self.conn is not None:
				print 'Connected by', addr
				break

		# data receiving
		while self.flag_stop is False:
				# parse
				data = self.get_data(self.conn)
				if len(data) == 0:
						break

				# process accacc data
				# print(data)
				self.process_data(data)

		if self.conn is not None:
			self.conn.close()
			self.conn = None

	def process_data(self, data):
		pon = ["ping", "pon ", "pan "]
		hz = data[0]
		power = data[1]
		if hz == 0.0:
			return
		one_period = 1.0/hz
		t = time.time()*1000
		# if elapsed time since last pon
		if t - self.time_last_pon > one_period*1000:
			# stroke power lager then 1.0 m/s^2
			if power > 1.0:
				self.time_last_pon = t - (t-self.time_last_pon-one_period*1000)
				index_pon = self.count_pon%len(pon)
				print("%s:%d" % (pon[index_pon], self.count_pon))
				if index_pon == 2:
					# vibrate 200millisec immediately
					self.send("vib,0,200\n")
				self.count_pon = self.count_pon + 1

	def send(self, data):
		if self.conn is not None:
			self.conn.send(data)

	def stop(self):
		self.flag_stop = True

# input "q" to quit, "v" to phone vibration.
if __name__ == "__main__":
	# set host and port
	host = "127.0.0.1"
	port = 12345

	server_thread = ServerThread(host, port)
	server_thread.start()

	while True:
		data = raw_input()
		command =  data.strip()
		if command == "q":
			break
		if command  == "v":
			# Android "vib,<sleep_millisec>,<vib_millisec>,<sleep_millisec>,<vib_millisec>,.. ,\n"
			# iPhone "vib\n" 
			# iPhone only permit user to vibrate once.
			server_thread.send("vib,200,500,200,500\n")

	server_thread.stop()

