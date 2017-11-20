try:
	import RPi.GPIO as GPIO
	from lib_nrf24 import NRF24
	from math import *
	import time
	import spidev
	import sys
	import os.path
	import pickle
	from threading import Thread

	def decompress(compressed):
		"""Decompress a list of output ks to a string."""
		from cStringIO import StringIO
		# Build the dictionary.
		dict_size = 256
		dictionary = dict((i, chr(i)) for i in xrange(dict_size))
	 
		# use StringIO, otherwise this becomes O(N^2)
		# due to string concatenation in a loop
		result = StringIO()
		w = chr(compressed.pop(0))
		result.write(w)
		for k in compressed:
			if k in dictionary:
				entry = dictionary[k]
			elif k == dict_size:
				entry = w + w[0]
			else:
				raise ValueError('Bad compressed k: %s' % k)
			result.write(entry)
	 
			# Add w+entry[0] to the dictionary.
			dictionary[dict_size] = w + entry[0]
			dict_size += 1
	 
			w = entry
		return result.getvalue()

	def decompressionOnTheGo(compressedFile, multList, multList_extended, value_n):

		#Open file to save the transmitted data
		outputFile = open("ReceivedFileCompressed1.txt", "wb")

		if(value_n > 2):
			multList_extended = [ik * 256 for ik in multList_extended]
			multList = [sum(xk) for xk in zip(multList, multList_extended)]

		new_mulData = [il * 256 for il in multList]
		toDecompress = [sum(x) for x in zip(compressedFile, new_mulData)]

		str_decompressed = decompress(toDecompress)
		outputFile.write(str_decompressed)
		outputFile.close()


	def main():	    

		GPIO.setmode(GPIO.BCM)
		GPIO.setup(22, GPIO.OUT)
		GPIO.output(22,1)
		GPIO.setup(23, GPIO.OUT)
		GPIO.output(23,1)
		GPIO.setup(24, GPIO.OUT)
		GPIO.output(24,1)

		print("Receiver")
		pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]
		payloadSize = 32
		channel_RX = 0x40
		channel_TX = 0x45

		#Initializa the radio transceivers with the CE ping connected to the GPIO22 and GPIO23
		radio_Tx = NRF24(GPIO, spidev.SpiDev())
		radio_Rx = NRF24(GPIO, spidev.SpiDev())
		radio_Tx.begin(0, 22)
		radio_Rx.begin(1, 23)

		#We set the Payload Size to the limit which is 32 bytes
		radio_Tx.setPayloadSize(payloadSize)
		radio_Rx.setPayloadSize(payloadSize)

		#We choose the channels to be used for one and the other transceiver
		radio_Tx.setChannel(channel_TX)
		radio_Rx.setChannel(channel_RX)

		#We set the Transmission Rate
		radio_Tx.setDataRate(NRF24.BR_250KBPS)
		radio_Rx.setDataRate(NRF24.BR_250KBPS)

		#Configuration of the power level to be used by the transceiver
		radio_Tx.setPALevel(NRF24.PA_MIN)
		radio_Rx.setPALevel(NRF24.PA_MIN)

		#We disable the Auto Acknowledgement
		radio_Tx.setAutoAck(False)
		radio_Rx.setAutoAck(False)
		radio_Tx.enableDynamicPayloads()
		radio_Rx.enableDynamicPayloads()

		#Open the writing and reading pipe
		radio_Tx.openWritingPipe(pipes[0])
		radio_Rx.openReadingPipe(0, pipes[1])

		#We print the configuration details of both transceivers
		#We print the configuration details of both transceivers
		print("Transmitter Details #################################################################################")
		radio_Tx.printDetails()
		print("*---------------------------------------------------------------------------------------------------*")
		print("Receiver Details ####################################################################################")
		radio_Rx.printDetails()
		print("*---------------------------------------------------------------------------------------------------*")

		###############################################################################################################################
		###############################################################################################################################
		###############################################################################################################################

		#Flag variables
		original_flag_data = 'A'
		flag = ""
		flag_n = 0

		#Packet related variables
		frame = []
		handshake_frame = []
		compressed = []
		multData = []
		multData_extended = []

		#ACK related variables
		time_ack = 0.5
		receivedPacket = 0
		receivedHandshakePacket = 0
		receivedLastControlPacket = 0

		start = time.time()
		#We listen for the control packet
		radio_Rx.startListening()
		while not (receivedHandshakePacket):
			str_Handshakeframe = ""

			if radio_Rx.available(0):
				radio_Rx.read(handshake_frame, radio_Rx.getDynamicPayloadSize())

				for c in range(0, len(handshake_frame)):
					str_Handshakeframe = str_Handshakeframe + chr(handshake_frame[c])

				#print("Handshake frame: " + str_Controlframe)
				if(len(str_Handshakeframe.split(",")) == 2):
					print("Sending ACK")
					radio_Tx.write(list("ACK"))
					numberOfPackets, n = str_Handshakeframe.split(",")
					n = int(n)
					indexing_0 = range(0, 31, int(n/8.5)+1)[0:]
					indexing_1 = range(1, 31, int(n/8.5)+1)[0:]
					if(n > 16):
						indexing_2 = range(2, 31, 3)[0:]
				
				else:
					if(chr(handshake_frame[0]) == original_flag_data):
						handshake_frame = handshake_frame[1:len(handshake_frame)]
						compressed.extend([handshake_frame[i] for i in indexing_0])
						multData.extend([handshake_frame[i] for i in indexing_1])
						if(n > 16):
							multData_extended.extend([handshake_frame[i] for i in indexing_2])
						radio_Tx.write(list("ACK") + list(original_flag_data))
						flag_n = (flag_n + 1) % 10
						nextIndexing = 1
						receivedHandshakePacket = 1

		print("Handshake done")
		print("The number of data packets that will be transmitted: " + numberOfPackets)
		print("maximum value of list: " + str(n))

		dec_ready = 0
		add = 0
		for i in range(0,int(numberOfPackets)-1):

			timeout = time.time() + time_ack
			flag = chr(ord(original_flag_data) + flag_n)

			while not (receivedPacket):
				if radio_Rx.available(0):
					radio_Rx.read(frame, radio_Rx.getDynamicPayloadSize())
					if(chr(frame[0]) == flag):

						frame = frame[1:len(frame)]
						if (nextIndexing == 0):

							compressed.extend([frame[i] for i in [i for i in indexing_0 if i < len(frame)]])
							multData.extend([frame[i] for i in [i for i in indexing_1 if i < len(frame)]])
							if(n > 16):
								multData_extended.extend([frame[i] for i in [i for i in indexing_2 if i < len(frame)]])
							nextIndexing = (nextIndexing + 1) % (int(n/8.5)+1)

						elif (nextIndexing == 1):

							if(n > 16):
								compressed.extend([frame[i] for i in [i for i in indexing_2 if i < len(frame)]])
								multData.extend([frame[i] for i in [i for i in indexing_0 if i < len(frame)]])
								multData_extended.extend([frame[i] for i in [i for i in indexing_1 if i < len(frame)]])
							else:
								compressed.extend([frame[i] for i in [i for i in indexing_1 if i < len(frame)]])
								multData.extend([frame[i] for i in [i for i in indexing_0 if i < len(frame)]])
							nextIndexing = (nextIndexing + 1) % (int(n/8.5)+1)

						else:
							compressed.extend([frame[i] for i in [i for i in indexing_1 if i < len(frame)]])
							multData.extend([frame[i] for i in [i for i in indexing_2 if i < len(frame)]])
							multData_extended.extend([frame[i] for i in [i for i in indexing_0 if i < len(frame)]])
							nextIndexing = (nextIndexing + 1) % (int(n/8.5)+1)

						if(dec_ready == 900):
							compressed = list(map(int, compressed))
							multData = list(map(int, multData))
							if(n > 16):
								multData_extended = list(map(int, multData_extended))
							thread = Thread(target = decompressionOnTheGo, args = (compressed, multData, multData_extended, int(n/8.5) + 1))
							thread.start()
							#decompressionOnTheGo(compressed, multData, multData_extended, int(n/8.5) + 1)
							add += 50
							dec_ready = 0
							print("On the way to the win")
						radio_Tx.write(list("ACK") + list(flag))
						receivedPacket = 1
					else:
						print("Wrong message -> asking for retransmission")
						if flag_n == 0:
							radio_Tx.write(list("ACK") + list('J'))
						else:
							radio_Tx.write(list("ACK") + list(chr(ord(original_flag_data) + flag_n-1)))
						timeout = time.time() + time_ack
			dec_ready += 1
			flag_n = (flag_n + 1) % 10
			receivedPacket = 0

		decompressionOnTheGo(compressed, multData, multData_extended, int(n/8.5) + 1)
		final = time.time()
		print("Total time: " + str(final-start))

		GPIO.output(22, 0)
		GPIO.output(23, 0)

	if __name__ == '__main__':
		main()

except KeyboardInterrupt:
	GPIO.output(22,0)
	GPIO.output(23,0)
	GPIO.output(24,0)
	GPIO.cleanup()