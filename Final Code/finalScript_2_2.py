try:
	import RPi.GPIO as GPIO
	from lib_nrf24 import NRF24
	from math import *
	import numpy as np
	import time
	import spidev
	import sys
	import os.path
	from threading import Thread, Event
	import nm_main as NetMode

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

	def decompressionOnTheGo(compressedList, listMax):

		compressedString = ""
		for c in range(0, len(compressedList)):
			compressedString += chr(compressedList[c])

		i = 0
		#compressedList += chr(0)
		strJoin = 0
		compde = []
		x = 0
		j = 0
		bitsMax = int(np.ceil(np.log(listMax+1)/np.log(2)))
		charLength = 8

		while i < (len(compressedString)*8/bitsMax):
		  if x < bitsMax:
			strJoin = (strJoin<<charLength) + ord(compressedString[j])
			x = x + charLength
			j = j + 1;
		  else:
			compde.append(strJoin>>(x-bitsMax))
			strJoin = strJoin & (2**(x-bitsMax)-1)
			i += 1
			x = x - bitsMax

		str_decompressed = decompress(compde)

		#Open file to save the transmitted data
		outputFile = open("RxFileMTP-GroupC-SR.txt", "wb")
		outputFile.write(str_decompressed)
		outputFile.close()


	def led_blink(time_onoff):

		global blink
		GPIO.setmode(GPIO.BCM)
		while(blink):
			GPIO.output(2, 1)
			time.sleep(time_onoff)
			GPIO.output(2, 0)
			time.sleep(time_onoff)
		return


	def main():
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(23, GPIO.OUT, initial=GPIO.LOW)
		GPIO.setup(22, GPIO.OUT, initial=GPIO.LOW)
		GPIO.setup(2, GPIO.OUT) #LED 1 TX_RX Running
		GPIO.setup(3, GPIO.OUT) #LED 2 End-of-File
		GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #ON or OFF
		GPIO.setup(14, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #Transmit or Receive
		GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #Network Mode

		GPIO.output(2, 0)
		GPIO.output(3, 0)

		TX0_RX1 = True
		global blink
		blink = 0

		led_thread2 = Thread(target = led_blink, args = (0.7, ))
		led_thread2.start()

		while True:
			input_onoff = GPIO.input(15)
			blink = 1
			if(input_onoff == False):
				time.sleep(1)
				print("Waiting to start")
			else:
				blink = 0
				break
		
		TX_RX = GPIO.input(14)
		NM = GPIO.input(18)

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
				channel_TX = 30
				channel_RX = 50

				#Initializa the radio transceivers with the CE ping connected to the GPIO22 and GPIO24
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
				radio_Tx.setDataRate(NRF24.BR_2MBPS)
				radio_Rx.setDataRate(NRF24.BR_2MBPS)

				#Configuration of the power level to be used by the transceiver
				radio_Tx.setPALevel(NRF24.PA_HIGH)
				radio_Rx.setPALevel(NRF24.PA_HIGH)

				#CRC Length
				radio_Tx.setCRCLength(NRF24.CRC_8)
				radio_Rx.setCRCLength(NRF24.CRC_8)

				#We disable the Auto Acknowledgement
				radio_Tx.setAutoAck(False)
				radio_Rx.setAutoAck(False)
				radio_Tx.enableDynamicPayloads()
				radio_Rx.enableDynamicPayloads()

				#Open the writing and reading pipe
				radio_Tx.openWritingPipe(pipe_Tx)
				radio_Rx.openReadingPipe(0, pipe_Rx)

				###############################################################################################################################
				###############################################################################################################################
				###############################################################################################################################

				#Read file to transmit
				inFile = open("MTP_Prev.txt", "rb")
				data2Tx = inFile.read()
				inFile.close()

				#flag variables
				original_flag = 'A'
				flag = ""
				ctrl_flag_n = 0
				flag_n = 0

				#packet realted variables
				overhead = 1
				dataSize = payloadSize - overhead
				dataControlSize = payloadSize - overhead
				#Data Packets
				packets = []
				finalData = ""
				numberofPackets = 0

				#ACK related variables
				ack = []
				handshake = []
				ctrl_ack = []
				ack_received = 0
				controlAck_received = 0
				handshakeAck_received = 0

				#Time variables
				time_ack = 0.08

				#LED Blinking thread
				led_thread = Thread(target = led_blink, args = (0.3, ))

				#Compression of the data to transmit into data2Tx_compressed
				data2Tx_compressed = compress(data2Tx)

				#Compression #########################################################################################################
				listLengh = len(data2Tx_compressed)
				listMax = max(data2Tx_compressed)
				bitsMax = int(np.ceil(np.log(listMax+1)/np.log(2)))
				charLength = 8
				data2Tx_compressed.append(0)

				remainded = bitsMax
				pad = bitsMax - charLength

				toSend = ""
				i = 0

				while i < listLengh :
					compJoin = (data2Tx_compressed[i] << bitsMax) + data2Tx_compressed[i+1]
					toSend += chr((compJoin>>(pad+remainded))%(2**charLength))
					remainded = remainded - charLength
					if remainded <=0:
						i=i+1
						remainded= remainded % bitsMax
						if remainded == 0:
						  remainded=bitsMax

				########################################################################################################################

				#Now we conform all the data packets in a list
				for i in range (0, len(toSend), dataSize):
					if((i+dataSize) < len(toSend)):
						packets.append(toSend[i:i+dataSize])
					else:
						packets.append(toSend[i:])
					numberofPackets += 1

				#Start sendind Handshake Packet
				handshakePacket = str(numberofPackets) + "," + str(listLengh) + "," + str(listMax)
				radio_Tx.write(handshakePacket)
				timeout = time.time() + time_ack
				radio_Rx.startListening()
				str_Handshake = ""
				blink = 1
				led_thread.start()

				print("Starting Script")

				###############################################################################################################################
				###############################################################################################################################
				###############################################################################################################################
				#While we don't receive the handshake ack we keep trying
				while not (handshakeAck_received):

					if radio_Rx.available(0):
						radio_Rx.read(handshake, radio_Rx.getDynamicPayloadSize())
						#print("Something Received")

						for c in range(0, len(handshake)):
							str_Handshake = str_Handshake + chr(handshake[c])

						#If the received ACK does not match the expected one we retransmit, else we set the received handshake ack to 1
						if(list(str_Handshake) != list("ACK")):	
							radio_Tx.write(handshakePacket)
							timeout = time.time() + time_ack
							#print("Handshake Message Lost")
							str_Handshake = ""
						else:
							#print("Handshake done")
							handshakeAck_received = 1

					#If an established time passes and we have not received anything we retransmit the handshake packet
					if((time.time()) > timeout):
						#print("No Handshake ACK received resending message")
						radio_Tx.write(handshakePacket)
						timeout = time.time() + time_ack

				messageSent = ""
				#We iterate over every packet to be sent
				suma = 0
				retrans = 0
				for message in packets:

					messageSent += message
					flag = chr(ord(original_flag) + flag_n)
					message2Send = list(flag) + list(message)
					radio_Tx.write(message2Send)

					timeout = time.time() + time_ack
					str_ack = ""

					#While we don't receive a correct ack for the transmitted packet we keep trying for the same packet
					while not (ack_received):
						if radio_Rx.available(0):
							radio_Rx.read(ack, radio_Rx.getDynamicPayloadSize())

							for c in range(0, len(ack)):
								str_ack = str_ack + chr(ack[c])

							#If the received ACK does not match the expected one we retransmit, else we set the received data ack to 1
							if(list(str_ack) != (list("ACK") + list(flag))):
								radio_Tx.write(message2Send)
								timeout = time.time() + time_ack
								suma += 1
								str_ack = ""

								if(suma > 50):
									time_ack += 0.05
									suma = 0
									if(time_ack > 0.2):
										time_ack = 0.2
								retrans += 1

							else:
								ack_received = 1

						#If an established time passes and we have not received anything we retransmit the data packet
						if((time.time()) > timeout):
							suma += 1
							radio_Tx.write(message2Send)
							timeout = time.time() + time_ack
							
					ack_received = 0
					flag_n = (flag_n + 1) % 10

				blink = 0

				print("Number of retransmissions = " + str(retrans))

				GPIO.output(3, 1)
				radio_Rx.stopListening()
				radio_Tx.end()
				radio_Rx.end()
				GPIO.output(22, 0)
				GPIO.output(23, 0)

				time.sleep(2)
				GPIO.cleanup()

			else:
				print("Receiver")
				pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]
				payloadSize = 32
				channel_RX = 30
				channel_TX = 50

				#Initializa the radio transceivers with the CE ping connected to the GPIO22 and GPIO24
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
				radio_Tx.setDataRate(NRF24.BR_2MBPS)
				radio_Rx.setDataRate(NRF24.BR_2MBPS)

				#Configuration of the power level to be used by the transceiver
				radio_Tx.setPALevel(NRF24.PA_HIGH)
				radio_Rx.setPALevel(NRF24.PA_HIGH)

				#CRC Length
				radio_Tx.setCRCLength(NRF24.CRC_8)
				radio_Rx.setCRCLength(NRF24.CRC_8)

				#We disable the Auto Acknowledgement
				radio_Tx.setAutoAck(False)
				radio_Rx.setAutoAck(False)
				radio_Tx.enableDynamicPayloads()
				radio_Rx.enableDynamicPayloads()

				#Open the writing and reading pipe
				radio_Tx.openWritingPipe(pipes[1])
				radio_Rx.openReadingPipe(0, pipes[0])

				###############################################################################################################################
				###############################################################################################################################
				###############################################################################################################################

				#Flag variables
				original_flag_data = 'A'
				flag = ""
				flag_n = 0
				ctrl_flag_n = 0

				#Packet related variables
				frame = []
				handshake_frame = []
				compressed = []
				str_compressed = ""

				#ACK related variables
				time_ack = 0.08
				receivedPacket = 0
				receivedHandshakePacket = 0

				#LED Blinking thread
				led_thread = Thread(target = led_blink, args = (0.3, ))

				radio_Rx.startListening()

				#We listen for the control packet
				while not (receivedHandshakePacket):
					str_Handshakeframe = ""

					if radio_Rx.available(0):
						radio_Rx.read(handshake_frame, radio_Rx.getDynamicPayloadSize())

						for c in range(0, len(handshake_frame)):
							str_Handshakeframe = str_Handshakeframe + chr(handshake_frame[c])

						#print("Handshake frame: " + str_Controlframe)
						if(len(str_Handshakeframe.split(",")) == 3):
							radio_Tx.write(list("ACK"))
							numberOfPackets, listLength, listMax = str_Handshakeframe.split(",")
							listLength = int(listLength)
							listMax = int(listMax)
						
						else:
							if(chr(handshake_frame[0]) == original_flag_data):
								handshake_frame = handshake_frame[1:len(handshake_frame)]
								compressed.extend(handshake_frame)
								blink = 1
								led_thread.start()

								radio_Tx.write(list("ACK") + list(original_flag_data))
								flag_n = (flag_n + 1) % 10
								receivedHandshakePacket = 1

				bitsMax = int(np.ceil(np.log(listMax+1)/np.log(2)))
				suma = 0
				for i in range(0, int(numberOfPackets)-1):

					timeout = time.time() + time_ack
					flag = chr(ord(original_flag_data) + flag_n)

					while not (receivedPacket):

						if radio_Rx.available(0):
							radio_Rx.read(frame, radio_Rx.getDynamicPayloadSize())
							#print(frame)

							if(chr(frame[0]) == flag):
								compressed.extend(frame[1:len(frame)])

								if (((len(compressed)*8) % (bitsMax*300)) == 0):
									thread = Thread(target = decompressionOnTheGo, args = (compressed, listMax))
									thread.start()
								radio_Tx.write(list("ACK") + list(flag))
								receivedPacket = 1

							else:
								suma += 1

					flag_n = (flag_n + 1) % 10
					receivedPacket = 0

				thread = Thread(target = decompressionOnTheGo, args = (compressed, listMax))
				thread.start()

				blink = 0

				print("Number of retransmissions = " + str(suma))

				GPIO.output(3, 1)
				radio_Rx.stopListening()
				radio_Tx.end()
				radio_Rx.end()
				GPIO.output(22, 0)
				GPIO.output(23, 0)

				time.sleep(2)
				GPIO.cleanup()

		else:
			print("Network Mode")
			NetMode.main_nm()

	if __name__ == '__main__':
		main()

except KeyboardInterrupt:
	GPIO.output(22,0)
	GPIO.output(23,0)
	GPIO.cleanup()
