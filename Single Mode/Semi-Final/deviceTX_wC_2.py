try:
	import RPi.GPIO as GPIO
	from lib_nrf24 import NRF24
	from math import *
	import time
	import spidev
	import sys
	import os.path
	import numpy as np
	import os

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

	def printSummary(file1, file2):
		"""
		printSummary() prints out the number of bytes in the original file and in
		the result file.

		@params: two files that are to be checked.
		@return: n/a.
		"""
		# Checks if the files exist in the current directory.
		if (not os.path.isfile(file1)) or (not os.path.isfile(file2)):
			printError(0)

		# Finds out how many bytes in each file.
		f1_bytes = os.path.getsize(file1)
		f2_bytes = os.path.getsize(file2)

		sys.stderr.write(str(file1) + ': ' + str(f1_bytes) + ' bytes\n')
		sys.stderr.write(str(file2) + ': ' + str(f2_bytes) + ' bytes\n')

	def main():		

		start = time.time()
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(23, GPIO.OUT)
		GPIO.output(23, 1)
		GPIO.setup(22, GPIO.OUT)
		GPIO.output(22, 1)
		GPIO.setup(2, GPIO.OUT) #LED 1 TX_RX Running
		GPIO.setup(3, GPIO.OUT) #LED 2 End-of-File

		GPIO.output(2, 0)
		GPIO.output(3, 0)

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
		radio_Tx.setPALevel(NRF24.PA_MIN)
		radio_Rx.setPALevel(NRF24.PA_MIN)

		#CRC Length
		radio_Tx.setCRCLength(NRF24.CRC_8)
		radio_Rx.setCRCLength(NRF24.CRC_8)

		#We disable the Auto Acknowledgement
		radio_Tx.setAutoAck(False)
		radio_Rx.setAutoAck(False)
		radio_Tx.enableDynamicPayloads()
		radio_Rx.enableDynamicPayloads()

		#Open the writing and reading pipe
		radio_Rx.openReadingPipe(0, pipe_Rx)
		radio_Tx.openWritingPipe(pipe_Tx)

		#We print the configuration details of both transceivers
		#radio_Tx.printDetails()
		#print("*------------------------------------------------------------------------------------------------------------*")
		#radio_Rx.printDetails()
		#print("*------------------------------------------------------------------------------------------------------------*")

		###############################################################################################################################
		###############################################################################################################################
		###############################################################################################################################

		#VARIABLES

		textFile = "MTP_Prev.txt"

		#Read file to transmit
		inFile = open(textFile, "rb")
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
		time_ack = 0.05

		#First time error solution
		firstTime_retransmissions = 0

		#Checksum comprovation
		receivedChecksum = 0
		last_ack = []
		checksum_str = ""
		alreadyReceivedChecksum = 0

		###############################################################################################################################
		###############################################################################################################################
		###############################################################################################################################

		start_c = time.time()
		#Compression of the data to transmit into data2Tx_compressed
		data2Tx_compressed = compress(data2Tx)

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

		final_c = time.time()
		print("Compression time: " + str(final_c-start_c))

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
		print("Waiting ACK")

		###############################################################################################################################
		###############################################################################################################################
		###############################################################################################################################
		#While we don't receive the handshake ack we keep trying
		while not (handshakeAck_received):

			if radio_Rx.available(0):
				radio_Rx.read(handshake, radio_Rx.getDynamicPayloadSize())
				radio_Rx.openReadingPipe(0, pipe_Rx)
				print("Something Received")

				for c in range(0, len(handshake)):
					str_Handshake = str_Handshake + chr(handshake[c])

				#If the received ACK does not match the expected one we retransmit, else we set the received handshake ack to 1
				if(list(str_Handshake) != list("ACK")):	
					radio_Tx.write(handshakePacket)
					timeout = time.time() + time_ack
					print("Handshake Message Lost")
					str_Handshake = ""
				else:
					print("Handshake done")
					handshakeAck_received = 1

			#If an established time passes and we have not received anything we retransmit the handshake packet
			if((time.time()) > timeout):
				#print("No Handshake ACK received resending message")
				firstTime_retransmissions += 1
				radio_Tx.write(handshakePacket)
				timeout = time.time() + time_ack

		messageSent = ""

		###############################################################################################################################
		###############################################################################################################################
		###############################################################################################################################

		#We iterate over every packet to be sent
		suma = 0
		for message in packets:

			messageSent += message
			flag = chr(ord(original_flag) + flag_n)
			message2Send = list(flag) + list(message)
			radio_Tx.write(message2Send)
			#time.sleep(1)

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
						radio_Tx.write(message2Send)
						timeout = time.time() + time_ack
						#print("Data ACK received but not the expected one --> resending message")
						suma += 1
						str_ack = ""

					else:
						ack_received = 1

				#If an established time passes and we have not received anything we retransmit the data packet
				if((time.time()) > timeout):
					#print("No Data ACK received resending message")
					suma += 1
					radio_Tx.write(message2Send)
					timeout = time.time() + time_ack
					
			ack_received = 0
			flag_n = (flag_n + 1) % 10

		final = time.time()
		totalTime = final - start
		print(totalTime)
		print(messageSent == toSend)
		print("Total retransmissions: " + str(suma))

		GPIO.output(3, 1)

		time.sleep(5)

		GPIO.output(22,0)
		GPIO.output(23,0)
		GPIO.cleanup()

	if __name__ == '__main__':
		main()
		
except KeyboardInterrupt:
	GPIO.output(22,0)
	GPIO.output(23,0)
	GPIO.cleanup()
