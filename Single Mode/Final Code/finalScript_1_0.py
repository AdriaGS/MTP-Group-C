try:
	import RPi.GPIO as GPIO
	from lib_nrf24 import NRF24
	from math import *
	import time
	import spidev
	import sys
	import os.path

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

	def decompressionOnTheGo(compressedFile, multiplicationList):

		#Open file to save the transmitted data
		outputFile = open("ReceivedFileCompressed1.txt", "wb")

		new_mulData = [il * 256 for il in multiplicationList]
		toDecompress = [sum(x) for x in zip(compressedFile, new_mulData)]

		str_decompressed = decompress(toDecompress)
		outputFile.write(str_decompressed)
		outputFile.close()

	def main():
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(22, GPIO.OUT)
		GPIO.setup(24, GPIO.OUT)
		GPIO.setup(16, GPIO.OUT) #LED 1 POWER ON
    	GPIO.setup(20, GPIO.OUT) #LED 2 TX_RX Running
    	GPIO.setup(20, GPIO.OUT) #LED 3 End-of-File
    	GPIO.setup(14, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #ON or OFF
    	GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #Transmit or Receive
    	GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #Network Mode

		GPIO.output(22, 1)
		GPIO.output(24, 1)

		TX0_RX1 = True

		while True:
			input_onoff= GPIO.input(15)
			input_tx_rx= GPIO.input(14)
			if(input_onoff == True):
				time.sleep(1)
				print("Waiting to start")
			else:
				TX_RX = input_txrx
				break

		if(TX_RX):
			print("Transmitter")
			pipe_Tx = [0xe7, 0xe7, 0xe7, 0xe7, 0xe7]
			pipe_Rx = [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]
			payloadSize = 32
			channel_TX = 0x20
			channel_RX = 0x25

			#Initialize the radio transceivers with the CE ping connected to the GPIO22 and GPIO24
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

			###############################################################################################################################
			###############################################################################################################################
			###############################################################################################################################

			#Read file to transmit
			#inFile = open("SampleTextFile1Mb.txt", "rb")
			inFile = open("SampleTextFile1Mb.txt", "rb")
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
			#Control Packets
			control_packets = []
			numberofControlPackets = 0
			#Data Packets
			packets = []
			numberofPackets = 0

			#ACK related variables
			ack = []
			handshake = []
			ctrl_ack = []
			ack_received = 0
			controlAck_received = 0
			handshakeAck_received = 0

			#Time variables
			time_ack = 0.5

			start_c = time.time()
			#Compression of the data to transmit into data2Tx_compressed
			data2Tx_compressed = compress(data2Tx)
			n=len(bin(max(data2Tx_compressed)))-2

			#Now we conform all the data packets in a list
			for i in range (0, len(data2Tx_compressed), dataSize):
				if((i+dataSize) < len(data2Tx_compressed)):
					packets.append(data2Tx_compressed[i:i+dataSize])
				else:
					packets.append(data2Tx_compressed[i:])
				numberofPackets += 1

			#We create the string with the packets needed to decompress the file transmitted
			controlList_extended = []
			controlList_mid = []
			controlList = []
			
			for val in data2Tx_compressed:
				division = int(val/256)
				controlList_mid.append(division)

			print("A")

			if(n > 16):
				for val in controlList_mid:
					division = int(val/256)
					controlList_extended.append(division)

			for val2 in controlList_mid:
				def_val = val2
				if val2 > 256:
					def_val -= 256
				controlList.append(def_val)

			controlList.extend(controlList_extended)

			final_c = time.time()
			print("Compression time: " + str(final_c-start_c))

			#Now we conform all the control packets in a list
			for x in range (0, len(controlList), dataControlSize):
				if((x+dataControlSize) < len(controlList)):
					control_packets.append(controlList[x:x+dataControlSize])
				else:
					control_packets.append(controlList[x:])
				numberofControlPackets += 1

			#Start time
			start = time.time()
			radio_Tx.write(str(numberofPackets) + "," + str(numberofControlPackets) + "," + str(n))
			timeout = time.time() + time_ack
			radio_Rx.startListening()
			str_Handshake = ""

			#While we don't receive the handshake ack we keep trying
			while not (handshakeAck_received):

				if radio_Rx.available(0):
					radio_Rx.read(handshake, radio_Rx.getDynamicPayloadSize())

					for c in range(0, len(handshake)):
						str_Handshake = str_Handshake + chr(handshake[c])

					#If the received ACK does not match the expected one we retransmit, else we set the received handshake ack to 1
					if(list(str_Handshake) != list("ACK")):												#####Can we avoid the for above? using directly ack received from .read()
						radio_Tx.write(str(numberofPackets) + "," + str(numberofControlPackets))
						timeout = time.time() + time_ack
						print("Handshake Message Lost")
						str_Handshake = ""
					else:
						print("Handshake done")
						handshakeAck_received = 1

				#If an established time passes and we have not received anything we retransmit the handshake packet
				if((time.time() + 0.2) > timeout):
					print("No Handshake ACK received resending message")
					radio_Tx.write(str(numberofPackets) + "," + str(numberofControlPackets))
					timeout = time.time() + time_ack

			#We send all control packets
			for controlMessage in control_packets:

				ctrl_flag = chr(ord(original_flag) + ctrl_flag_n)
				ctrlMessage = list(ctrl_flag) + controlMessage
				#print(ctrlMessage)
				radio_Tx.write(list(ctrlMessage))

				timeout = time.time() + time_ack
				radio_Rx.startListening()
				str_controlAck = ""

				#While we don't receive a correct ack for the transmitted packet we keep trying for the same packet
				while not (controlAck_received):
					#time.sleep(1)

					if radio_Rx.available(0):
						radio_Rx.read(ctrl_ack, radio_Rx.getDynamicPayloadSize())

						for c in range(0, len(ctrl_ack)):
							str_controlAck = str_controlAck + chr(ctrl_ack[c])

						#If the received ACK does not match the expected one we retransmit, else we set the received control ack to 1
						if(list(str_controlAck) != (list("ACK") + list(ctrl_flag))):
							radio_Tx.write(ctrlMessage)
							timeout = time.time() + time_ack
							print("Control ACK received but not the expected one --> resending message")
							str_controlAck = ""
						else:
							controlAck_received = 1

					#If an established time passes and we have not received anything we retransmit the control packet
					if((time.time() + 0.2) > timeout):
						print("No Control ACK received --> resending message")
						radio_Tx.write(ctrlMessage)
						timeout = time.time() + time_ack

				controlAck_received = 0
				ctrl_flag_n = (ctrl_flag_n + 1) % 10

			#We iterate over every packet to be sent
			dec_ready = 0
			for message in packets:

				flag = chr(ord(original_flag) + flag_n)
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

			#print(controlList)

			final = time.time()
			totalTime = final - start
			print(totalTime)

			GPIO.output(22, 0)
			GPIO.output(24, 0)

		else:
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
			radio_Tx.setPALevel(NRF24.PA_LOW)
			radio_Rx.setPALevel(NRF24.PA_LOW)

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
			original_flag = 'A'
			flag = ""
			flag_n = 0
			ctrl_flag_n = 0

			#Packet related variables
			frame = []
			ctrlFrame = []
			handshake_frame = []
			compressed = []
			multiplicationData = []

			#ACK related variables
			time_ack = 0.5
			receivedPacket = 0
			receivedHandshakePacket = 0
			receivedControlPacket = 0

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
					print("Handshake received sending ACK")
					radio_Tx.write(list("ACK"))
					receivedHandshakePacket = 1

			numberOfPackets, numberofControlPackets, n = str_Handshakeframe.split(",")
			print("The number of control packets that will be transmitted: " + numberofControlPackets)
			print("The number of data packets that will be transmitted: " + numberOfPackets)
			print("maximum value of list: " + n)
			
			radio_Rx.startListening()

			#For all the control packets that are to be received we send a control ack for every one we receive correctly
			for x in range(0, int(numberofControlPackets)):

				ctrl_flag = chr(ord(original_flag) + ctrl_flag_n)
				timeout = time.time() + time_ack

				#While we don't receive the expected control packet we keep trying
				while not (receivedControlPacket):
					str_controlFrame = ""
					if radio_Rx.available(0):
						radio_Rx.read(ctrlFrame, radio_Rx.getDynamicPayloadSize())

						#We check if the received packet is the expected one
						if(chr(ctrlFrame[0]) == ctrl_flag):
							multiplicationData.extend(ctrlFrame[1:len(ctrlFrame)])
							radio_Tx.write(list("ACK") + list(ctrl_flag))
							receivedControlPacket = 1
						else:
							#print("Message received but not the expected one -> retransmit please")
							if ctrl_flag_n == 0:
								radio_Tx.write(list("ACK") + list('J'))
							else:
								radio_Tx.write(list("ACK") + list(chr(ord(original_flag) + ctrl_flag_n-1)))
							timeout = time.time() + time_ack

				ctrl_flag_n = (ctrl_flag_n + 1) % 10
				receivedControlPacket = 0

			multiplicationData = list(map(int, multiplicationData))
			if(int(n)>16):
				multiplicationData_mid = [ik * 256 for ik in multiplicationData[len(multiplicationData)/2:len(multiplicationData)]]
				multiplicationData = [sum(xk) for xk in zip(multiplicationData[0:len(multiplicationData)/2], multiplicationData_mid)]

			dec_ready = 0
			add = 0
			for i in range(0,int(numberOfPackets)):
				timeout = time.time() + time_ack
				flag = chr(ord(original_flag) + flag_n)
				while not (receivedPacket):
					if radio_Rx.available(0):
						#print("RECEIVED PKT")
						radio_Rx.read(frame, radio_Rx.getDynamicPayloadSize())
						if(chr(frame[0]) == flag):
							compressed.extend(frame[1:len(frame)])
							if(dec_ready == 200 + add):
								compressed = list(map(int, compressed))
								decompressionOnTheGo(compressed, multiplicationData[0:len(compressed)])
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
								radio_Tx.write(list("ACK") + list(chr(ord(original_flag) + flag_n-1)))
							timeout = time.time() + time_ack
				dec_ready += 1
				flag_n = (flag_n + 1) % 10
				receivedPacket = 0

			compressed = list(map(int, compressed))
			decompressionOnTheGo(compressed, multiplicationData)
			final = time.time()
			print("Total time: " + str(final-start))

			GPIO.output(22, 0)
			GPIO.output(24, 0)

	if __name__ == '__main__':
	main()

except KeyboardInterrupt:
	GPIO.output(22,0)
	GPIO.output(24,0)
	GPIO.cleanup()