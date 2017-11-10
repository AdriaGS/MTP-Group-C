import RPi.GPIO as GPIO
from lib_nrf24 import NRF24
from math import *
import time
import spidev
import sys
import os.path
import numpy
import pickle
import sqlite3
import mat4py as m4p
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

	GPIO.setmode(GPIO.BCM)
	GPIO.setup(24, GPIO.OUT)
	GPIO.output(24,1)
	GPIO.setup(22, GPIO.OUT)
	GPIO.output(22, 1)

	print("Transmitter")
	pipe_Tx = [0xe7, 0xe7, 0xe7, 0xe7, 0xe7]
	pipe_Rx = [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]
	payloadSize = 32
	channel_TX = 0x60
	channel_RX = 0x65

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
	radio_Tx.setPALevel(NRF24.PA_LOW)
	radio_Rx.setPALevel(NRF24.PA_LOW)

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

	original_flag = 'A'
	flag = ""
	ctrl_flag_n = 0
	flag_n = 0
	overhead = 1
	time_ack = 0.5
	ack = []
	ack_received = 0
	controlAck_received = 0
	handshakeAck_received = 0
	inFile = open("ElQuijote.txt", "rb")
	data2Tx = inFile.read()
	inFile.close()
	packets = []
	control_packets = []
	numberofPackets = 0
	numberofControlPackets = 0

	data2Tx_compressed = compress(data2Tx)

	dataSize = payloadSize - overhead
	#Now we conform all the data packets in a list
	for i in range (0, len(data2Tx_compressed), dataSize):
		if((i+dataSize) < len(data2Tx_compressed)):
			packets.append(data2Tx_compressed[i:i+dataSize])
		else:
			packets.append(data2Tx_compressed[i:])
		numberofPackets += 1

	#Now we conform all the control packets in a list
	controlList = ""
	
	for val in data2Tx_compressed:
		controlList += str(int(val/256))

	dataControlSize = payloadSize - overhead
	#Now we conform all the packets in a list
	for x in range (0, len(controlList), dataControlSize):
		if((i+dataControlSize) < len(controlList)):
			control_packets.append(controlList[x:x+dataControlSize])
		else:
			control_packets.append(controlList[x:])
		numberofControlPackets += 1

	#Start time
	start = time.time()
	radio_Tx.write(str(numberofPackets) + "," + str(numberofControlPackets))
	timeout = time.time() + time_ack
	radio_Rx.startListening()
	str_ack = ""
	while not (handshakeAck_received):
		if radio_Rx.available(0):
			radio_Rx.read(ack, radio_Rx.getDynamicPayloadSize())
			for c in range(0, len(ack)):
				str_ack = str_ack + chr(ack[c])
			if(list(str_ack) != list("ACK")):
				radio_Tx.write(str(numberofPackets))
				timeout = time.time() + time_ack
				print("Handshake Message Lost")
				str_ack = ""
			else:
				print("Handshake accomplished")
				handshakeAck_received = 1
		if((time.time() + 0.01) > timeout):
			print("No Control ACK received resending message")
			radio_Tx.write(str(numberofPackets))
			timeout = time.time() + time_ack

	for controlMessage in control_packets:
		ctrl_flag = chr(ord(original_flag) + ctrl_flag_n)
		ctrlMessage = list(ctrl_flag) + controlMessage
		radio_Tx.write(ctrlMessage)
		timeout = time.time() + time_ack
		radio_Rx.startListening()
		str_ack = ""
		while not (controlAck_received):
			time.sleep(1)
			if radio_Rx.available(0):
				radio_Rx.read(ack, radio_Rx.getDynamicPayloadSize())
				for c in range(0, len(ack)):
					str_ack = str_ack + chr(ack[c])
				if(list(str_ack) != (list("ACK") + list(ctrl_flag))):
					radio_Tx.write(list(ctrl_flag) + controlMessage)
					timeout = time.time() + time_ack
					print("Control Message Lost")
					str_ack = ""
				else:
					controlAck_received = 1
			if((time.time() + 0.01) > timeout):
				print("No Control ACK received resending message")
				radio_Tx.write(str(numberofPackets))
				timeout = time.time() + time_ack
		controlAck_received = 0
		ctrl_flag_n = (ctrl_flag_n + 1) % 10

	#We iterate over every packet to be sent
	for message in packets:
		flag = chr(ord(original_flag) + flag_n)
		message2Send = list(flag) + message
		radio_Tx.write(message2Send)
		#time.sleep(1)
		timeout = time.time() + time_ack
		radio_Rx.startListening()
		str_ack = ""
		while not (ack_received):
			if radio_Rx.available(0):
				radio_Rx.read(ack, radio_Rx.getDynamicPayloadSize())
				for c in range(0, len(ack)):
					str_ack = str_ack + chr(ack[c])
				#print("ACK received: " + str_ack)
				if(list(str_ack) != (list("ACK") + list(flag))):
					#print(list("ACK") + list(flag))
					radio_Tx.write(list(flag) + list(message))
					timeout = time.time() + time_ack
					print("Message Lost")
					str_ack = ""
				else:
					ack_received = 1
			if((time.time() + 0.2) > timeout):
				print("No ACK received resending message")
				radio_Tx.write(message2Send)
				timeout = time.time() + time_ack
		ack_received = 0
		flag_n = (flag_n + 1) % 10

	final = time.time()
	totalTime = final - start
	print(totalTime)

if __name__ == '__main__':
	main()
	

