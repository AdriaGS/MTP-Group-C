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
	flag_n = 0
	overhead = 1
	time_ack = 0.5
	ack = []
	ack_received = 0
	controlAck_received = 0
	inFile = open("ElQuijote.txt", "rb")
	data2Tx = inFile.read()
	inFile.close()
	packets = []
	numberofPackets = 0
	numberofControlPackets = 0

	data2Tx_compressed = compress(data2Tx)
	division = ""
	i = 0

	print(len(data2Tx_compressed))
	
	for val in data2Tx_compressed:
		division += (chr(int(val/256)))

	#print(division)

	dataControlSize = payloadSize
	#Now we conform all the packets in a list
	for i in range (0, len(division), dataControlSize):
		if((i+dataControlSize) < len(division)):
			packets.append(division[i:i+dataControlSize])
		else:
			packets.append(division[i:])
		numberofControlPackets += 1

	dataSize = payloadSize - overhead
	#Now we conform all the packets in a list
	for i in range (0, len(data2Tx_compressed), dataSize):
		if((i+dataSize) < len(data2Tx_compressed)):
			packets.append(data2Tx_compressed[i:i+dataSize])
		else:
			packets.append(data2Tx_compressed[i:])
		numberofPackets += 1
	
	print(numberofPackets)
	print(numberofControlPackets)
	#Start time
	start = time.time()
	#We send a first packet to tell the receiver how many packets we'll be sending
	radio_Tx.write(str(numberofPackets))
	#time.sleep(1)
	timeout = time.time() + time_ack
	radio_Rx.startListening()
	str_ack = ""
	while not (controlAck_received):
		if radio_Rx.available(0):
			radio_Rx.read(ack, radio_Rx.getDynamicPayloadSize())
			for c in range(0, len(ack)):
				str_ack = str_ack + chr(ack[c])
			if(list(str_ack) != list("ACK")):
				radio_Tx.write(str(numberofPackets))
				timeout = time.time() + time_ack
				print("Control Message Lost")
				str_ack = ""
			else:
				controlAck_received = 1
		if((time.time() + 0.01) > timeout):
			print("No Control ACK received resending message")
			radio_Tx.write(str(numberofPackets))
			timeout = time.time() + time_ack

	#We iterate over every packet to be sent
	for message in packets:
		flag = chr(ord(original_flag) + flag_n)
		message2Send = list(flag) + message
		#print(message2Send)
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
	

