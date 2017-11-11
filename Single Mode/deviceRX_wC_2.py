import RPi.GPIO as GPIO
from lib_nrf24 import NRF24
from math import *
import time
import spidev
import sys
import os.path
import pickle

def decompress(compressed):
    """Decompress a list of output ks to a string."""
    from cStringIO import StringIO
 
    # Build the dictionary.
    dict_size = 256
    dictionary = dict((i, chr(i)) for i in xrange(dict_size))
    # in Python 3: dictionary = {i: chr(i) for i in range(dict_size)}
 
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

def main():	    
	GPIO.setmode(GPIO.BCM)
	GPIO.setup(24, GPIO.OUT)
	GPIO.output(24,1)
	GPIO.setup(22, GPIO.OUT)
	GPIO.output(22,1)

	print("Receiver")
	pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]
	payloadSize = 32
	channel_RX = 0x20
	channel_TX = 0x25

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

	#Open file to save the transmitted data
	outputFile = open("RxFileCompressed2.txt", "wb")

	#Flag variables
	original_flag = 'A'
	flag = ""
	flag_n = 0
	ctrl_flag_n = 0

	#Packet related variables
	frame = []
	handshake_frame = []
	compressed = []

	#ACK related variables
	time_ack = 0.5
	receivedPacket = 0
	receivedHandshakePacket = 0

	#We listen for the control packet
	radio_Rx.startListening()
	while not (receivedHandshakePacket):
		str_Handshakeframe = ""

		if radio_Rx.available(0):
			radio_Rx.read(handshake_frame, radio_Rx.getDynamicPayloadSize())

			for c in range(0, len(handshake_frame)):
				str_Handshakeframe = str_Handshakeframe + chr(handshake_frame[c])

			#print("Handshake frame: " + str_Controlframe)
			print("Handshake received sending ACK")
			radio_Tx.write(list("ACK"))
			receivedHandshakePacket = 1

	numberOfPackets = int(str_Handshakeframe)
	print("The number of data packets that will be transmitted: " + str(numberOfPackets))

	radio_Rx.startListening()

	for i in range(0, numberOfPackets):

		timeout = time.time() + time_ack
		flag = chr(ord(original_flag) + flag_n)

		while not (receivedPacket):

			if radio_Rx.available(0):
				radio_Rx.read(frame, radio_Rx.getDynamicPayloadSize())

				if(chr(frame[0]) == flag):
					compressed.extend(frame[1:len(frame)])
					radio_Tx.write(list("ACK") + list(flag))
					receivedPacket = 1
				else:
					print("Wrong message -> asking for retransmission")
					if flag_n == 0:
						radio_Tx.write(list("ACK") + list('J'))
					else:
						radio_Tx.write(list("ACK") + list(chr(ord(original_flag) + flag_n-1)))
					timeout = time.time() + time_ack

		flag_n = (flag_n + 1) % 10
		receivedPacket = 0


	#Decompression postprocessing
	toDecompress_mid = []
	pos = 0
	for x in compressed:
		binary = bin(x)
		binary = binary[2:len(binary)]
		bitLength = len(binary)

		if(pos != (len(compressed)-1)):
			for i in range(0, 8-bitLength):
				binary = "0" + binary
		else:
			for i in range(0, (len(lista)*(n+1) - (pos)*8) - bitLength):
				binary = "0" + binary

		toDecompress_mid.extend(list(binary))
		pos += 1

	toDecompress_mid = list(map(int, toDecompress_mid))

	#print(toDecompress_mid)

	toDecompress = []
	for j in range(0, len(toDecompress_mid), n+1):
		l = toDecompress_mid[j: j+(n+1)]
		value = 0
		for k in range(0, len(l)):
			value += (int(l[k]) * 2**(n-k))		
	toDecompress.append(value)

	str_decompressed = decompress(toDecompress)
	outputFile.write(str_decompressed)
	outputFile.close()

if __name__ == '__main__':
	main()
