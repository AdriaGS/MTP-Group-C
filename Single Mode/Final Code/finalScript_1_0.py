try:
	import RPi.GPIO as GPIO
	from lib_nrf24 import NRF24
	from math import *
	import time
	import spidev
	import sys
	import os.path
	from threading import Thread, Event

	def compress(uncompressed):
		"""Compress a string to a list of output symbols."""
	 
		# Build the dictionary.
		dict_size = 256
		dictionary = {chr(i): i for i in range(dict_size)}
		#dictionary = dict((chr(i), i) for i in xrange(dict_size))
		# in Python 3: dictionary = {chr(i): i for i in range(dict_size)}
	 
		w = ""
		result = []
		for c in uncompressed:
			wc = w + c
			if wc in dictionary:
				w = wc
			else:
				result.append(dictionary[w])
				# Add wc to the dictionary.
				dictionary[wc] = dict_size
				dict_size += 1
				w = c
	 
		# Output the code for w.
		if w:
			result.append(dictionary[w])
		return result

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
		outputFile = open("Rx-File_SM-GroupC.txt", "wb")

		if(value_n > 2):
			multList_extended = [ik * 256 for ik in multList_extended]
			multList = [sum(xk) for xk in zip(multList, multList_extended)]

		new_mulData = [il * 256 for il in multList]
		toDecompress = [sum(x) for x in zip(compressedFile, new_mulData)]

		str_decompressed = decompress(toDecompress)
		outputFile.write(str_decompressed)
		outputFile.close()

	def led_blink(gpio_value, stop_event):

		while(not stop_event.is_set()):
			GPIO.output(gpio_value, 1)
			time.sleep(0.5)
			GPIO.output(gpio_value, 0)
			time.sleep(0.5)

	def main():
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(22, GPIO.OUT)
		GPIO.setup(24, GPIO.OUT)
    	GPIO.setup(2, GPIO.OUT) #LED 1 TX_RX Running
    	GPIO.setup(3, GPIO.OUT) #LED 2 End-of-File
    	GPIO.setup(14, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #ON or OFF
    	GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #Transmit or Receive
    	GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #Network Mode

		GPIO.output(22, 1)
		GPIO.output(24, 1)

		TX0_RX1 = True

		while True:
			input_onoff = GPIO.input(14)
			input_tx_rx = GPIO.input(15)
			input_nm = GPIO.input(18)
			if(input_onoff == True):
				time.sleep(1)
				print("Waiting to start")
			else:
				TX_RX = input_txrx
				NM = input_nm
				break

		if(not NM):
			#Single Mode Code
			########################################
			########################################
			########################################
			if(TX_RX):
				print("Transmitter")
				pipe_Tx = [0xe7, 0xe7, 0xe7, 0xe7, 0xe7]
				pipe_Rx = [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]
				payloadSize = 32
				channel_TX = 0x40
				channel_RX = 0x45

				#Initializa the radio transceivers with the CE ping connected to the GPIO22 and GPIO24
				radio_Tx = NRF24(GPIO, spidev.SpiDev())
				radio_Rx = NRF24(GPIO, spidev.SpiDev())
				radio_Tx.begin(0, 22)
				radio_Rx.begin(1, 24)

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
				radio_Tx.openWritingPipe(pipe_Tx)
				radio_Rx.openReadingPipe(1, pipe_Rx)

				#We print the configuration details of both transceivers
				radio_Tx.printDetails()
				print("*------------------------------------------------------------------------------------------------------------*")
				radio_Rx.printDetails()
				print("*------------------------------------------------------------------------------------------------------------*")

				###############################################################################################################################
				###############################################################################################################################
				###############################################################################################################################

				#Read file to transmit
				#inFile = open("SampleTextFile1Mb.txt", "rb")
				inFile = open("MTP_Prev.txt", "rb")
				data2Tx = inFile.read()
				inFile.close()

				#flag variables
				original_flag_data = 'A'
				flag = ""
				flag_n = 0

				#packet realted variables
				overhead = 1
				dataSize = payloadSize - overhead
				dataControlSize = payloadSize - overhead
				#Data Packets
				packets = []
				numberofPackets = 0

				#ACK related variables
				ack = []
				handshake = []
				ack_received = 0
				handshakeAck_received = 0

				#Time variables
				time_ack = 0.5

				#LED Blinking thread
				led_1 = Event()
				led_thread = Thread(target = led_blink, args = (2, led_1))

				start_c = time.time()
				#Compression of the data to transmit into data2Tx_compressed
				data2Tx_compressed = compress(data2Tx)
				n=len(bin(max(data2Tx_compressed)))-2

				#We create the string with the packets needed to decompress the file transmitted
				controlList_extended = []
				controlList = []
				
				for val in data2Tx_compressed:
					division = int(val/256)
					controlList.append(division)

				if(n > 16):
					for val in controlList_mid:
						division = int(val/256)
						controlList_extended.append(division)

				final_c = time.time()
				print("Compression time: " + str(final_c-start_c))

				data2Send = []
				for iterator in range(0, len(controlList)):
					data2Send.append(data2Tx_compressed[iterator])
					data2Send.append(controlList[iterator])
					if(n > 16):
						data2Send.append(controlList_extended[iterator])

				#Now we conform all the data packets in a list
				for i in range (0, len(data2Send), dataSize):
					if((i+dataSize) < len(data2Send)):
						packets.append(data2Send[i:i+dataSize])
					else:
						packets.append(data2Send[i:])
					numberofPackets += 1


				#Start time
				start = time.time()
				radio_Tx.write(str(numberofPackets) + "," + str(n))
				timeout = time.time() + time_ack
				radio_Rx.startListening()
				str_Handshake = ""

				#While we don't receive the handshake ack we keep trying
				while not (handshakeAck_received):

					if radio_Rx.available(0):
						radio_Rx.read(handshake, radio_Rx.getDynamicPayloadSize())

						for c in range(0, len(handshake)):
							str_Handshake = str_Handshake + chr(handshake[c])

						print(str_Handshake)

						#If the received ACK does not match the expected one we retransmit, else we set the received handshake ack to 1
						if(list(str_Handshake) != list("ACK")):	
							radio_Tx.write(str(numberofPackets) + "," + str(n))
							timeout = time.time() + time_ack
							print("Handshake Message Lost")
							str_Handshake = ""
						else:
							print("Handshake done")
							handshakeAck_received = 1

					#If an established time passes and we have not received anything we retransmit the handshake packet
					if((time.time() + 0.01) > timeout):
						print("No Handshake ACK received resending message")
						radio_Tx.write(str(numberofPackets) + "," + str(n))
						timeout = time.time() + time_ack

				led_thread.start()
				#We iterate over every packet to be sent
				dec_ready = 0
				for message in packets:

					flag = chr(ord(original_flag_data) + flag_n)
					message2Send = list(flag) + message
					radio_Tx.write(message2Send)

					if(dec_ready == 200):
						time.sleep(0.3)
						dec_ready = 0

					timeout = time.time() + time_ack
					radio_Rx.startListening()
					str_ack = ""

					#While we don't receive a correct ack for the transmitted packet we keep trying for the same packet
					while not (ack_received):
						if radio_Rx.available(0):
							radio_Rx.read(ack, radio_Rx.getDynamicPayloadSize())

							for c in range(0, len(ack)):
								str_ack = str_ack + chr(ack[c])

							#If the received ACK does not match the expected one we retransmit, else we set the received data ack to 1
							if(list(str_ack) != (list("ACK") + list(flag))):
								radio_Tx.write(list(flag) + list(message))
								timeout = time.time() + time_ack
								#print("Data ACK received but not the expected one --> resending message")
								str_ack = ""
							else:
								ack_received = 1

						#If an established time passes and we have not received anything we retransmit the data packet
						if((time.time() + 0.01) > timeout):
							#print("No Data ACK received resending message")
							radio_Tx.write(message2Send)
							timeout = time.time() + time_ack
					
					dec_ready = 0
					ack_received = 0
					flag_n = (flag_n + 1) % 10


				final = time.time()
				totalTime = final - start
				led_1.set()
				print(totalTime)

				GPIO.output(3, 1)
				GPIO.output(22, 0)
				GPIO.output(24, 0)

			else:
				print("Receiver")
				pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]
				payloadSize = 32
				channel_RX = 0x40
				channel_TX = 0x45

				#Initializa the radio transceivers with the CE ping connected to the GPIO22 and GPIO24
				radio_Tx = NRF24(GPIO, spidev.SpiDev())
				radio_Rx = NRF24(GPIO, spidev.SpiDev())
				radio_Tx.begin(0, 22)
				radio_Rx.begin(1, 24)

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
				radio_Tx.openWritingPipe(pipes[1])
				radio_Rx.openReadingPipe(1, pipes[0])

				#We print the configuration details of both transceivers
				radio_Tx.printDetails()
				print("*------------------------------------------------------------------------------------------------------------*")
				radio_Rx.printDetails()
				print("*------------------------------------------------------------------------------------------------------------*")

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

				#LED Blinking thread
				led_1 = Event()
				led_thread = Thread(target = led_blink, args = (2, led_1))

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
				led_thread.start()
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
								#print("Wrong message -> asking for retransmission")
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
				led_1.set()

				GPIO.output(3, 1)
				GPIO.output(22, 0)
				GPIO.output(24, 0)

		else:
			#Network Mode Code
			########################################
			########################################
			########################################

	if __name__ == '__main__':
	main()

except KeyboardInterrupt:
	GPIO.output(22,0)
	GPIO.output(24,0)
	GPIO.cleanup()