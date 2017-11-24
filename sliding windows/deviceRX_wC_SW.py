try:
	import RPi.GPIO as GPIO
	from lib_nrf24 import NRF24
	import time
	import spidev
	import numpy as np
	from threading import Thread
	import Queue
	myQueue = Queue()
	myQueue2 = Queue()

	def decompress(compressed):
		"""Decompress a list of output ks to a string."""
		from cStringIO import StringIO
	
		# Build the dictionary.
		dict_size = 256
		dictionary = {i: chr(i) for i in range(dict_size)}
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

	def decodingOnTheGo(listMax):

		#Open file to save the transmitted data
		###################
		i = 0
		strJoin = 0
		compde = []
		x = 0
		j = 0
		global myQueue2
		
		NewLength = int(np.ceil(np.log(listMax+1)/np.log(2)))
		OriginalLength=8;
		numPacketsOutput= len(compressedList)*OriginalLength/NewLength

		while i < (numPacketsOutput):
			if x < NewLength:
				strJoin = (strJoin<<OriginalLength) + ord(myQueue.get())
				x = x + OriginalLength
				j = j + 1;
			elif (x >= NewLength):
				myQueue2.put(strJoin>>(x-NewLength))
				strJoin = strJoin & (2**(x-NewLength)-1)
				i += 1
				x = x - NewLength
			myQueue.task_done()
	def decompresionOnTheGo	(listMax):	
		##Mirar si hay conflicots con windows o donde sea por no usar binario.
		outputFile = open("ReceivedFileCompressed2.txt", "a")
		##############
		"""Decompress a list of output ks to a string."""
	
		# Build the dictionary.
		dict_size = 256
		# in Python 2: dictionary = {i: chr(i) for i in range(dict_size)}
		dictionary = {i: chr(i) for i in range(dict_size)}
	 
		# use StringIO, otherwise this becomes O(N^2)
		# due to string concatenation in a loop
		w = chr(myQueue2.get())
		outputFile.write(w)
		myQueue2.task_done()
		while(1):
			k=myQueue2.get()
			if k in dictionary:
				entry = dictionary[k]
			elif k == dict_size:
				entry = w + w[0]
			else:
				raise ValueError('Bad compressed k: %s' % k)
			outputFile.write(entry)
			myQueue2.task_done()
			# Add w+entry[0] to the dictionary.
			dictionary[dict_size] = w + entry[0]
			dict_size += 1
			w = entry
#############
		outputFile.close()

	def length_OToN(compressedList, OriginalLength, NewLength ):
		i = 0
		strJoin = 0
		compde = []
		x = 0
		j = 0
		numPacketsOutput= len(compressedList)*OriginalLength/NewLength
		compressedList.append(0)

		while i < (numPacketsOutput):
			if x < NewLength:
				strJoin = (strJoin<<OriginalLength) + ord(compressedList[j])
				x = x + OriginalLength
				j = j + 1;
			else:
				compde.append(strJoin>>(x-NewLength))
				strJoin = strJoin & (2**(x-NewLength)-1)
				i += 1
				x = x - NewLength
		return compde

	def init():
		start = time.time()
		GPIO.setmode(GPIO.BCM)
		GPIO.setup(23, GPIO.OUT)
		GPIO.output(23,1)
		GPIO.setup(22, GPIO.OUT)
		GPIO.output(22,1)
		GPIO.setup(24, GPIO.OUT)
		GPIO.output(24,1)

		print("Receiver")
		pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]
		payloadSize = 32
		channel_RX = 90
		channel_TX = 100

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
		radio_Rx.openReadingPipe(0, pipes[0])

		#We print the configuration details of both transceivers
		radio_Tx.printDetails()
		print("*------------------------------------------------------------------------------------------------------------*")
		radio_Rx.printDetails()
		print("*------------------------------------------------------------------------------------------------------------*")
		
		return (radio_Tx,radio_Rx)
	
	def handshakeF(radio_Tx,radio_Rx,time_ack):	
		n=1
		while (1):
			if(n==1):
				print("Start handshake:")
				##STEP 1
				print("STEP 1: sending SYN")
				radio_Tx.write(list(chr(255)))
				timeout = time.time() + time_ack
				radio_Rx.startListening() #pasa algo?¿
				str_Handshake = ""
			if(n==2)
				print("STEP 2: Waiting ACK")
				##STEP 2
				while (true):
					str_Handshakeframe=""
					if radio_Rx.available(0):
						radio_Rx.read(handshake, radio_Rx.getDynamicPayloadSize())
						print("Something Received")
						if(list(handshake[0]!=254):	
						#If the received ACK does not match the expected one we retransmit, else we set the received handshake
							print("Handshake FAIL, retransmiting")
							n=1
							break
						elif(handshake[0]==254):
							for c in range(1, len(handshake)):
								str_Handshake = str_Handshake + chr(handshake[c])
							#Get parameters from tx
							numberOfPackets, listLength, listMax, slidingWindowsLength = str_Handshakeframe.split(",")
							listLength = int(listLength)
							listMax = int(listMax)
							slidingWindowsLength=int(slidingWindowsLength)
							numberOfPackets=int(numberOfPackets)
							n=3
							break							
					#If an established time passes and we have not received anything we retransmit the handshake packet
					if((time.time()) > timeout):
						print("No Handshake ACK received resending message")
						n=1
						break
			if(n==3)
				#STEP 3
				print("STEP 3: Sending ACK")
				radio_Tx.write(chr(253))
				print("HANDSHAKE DONE")
				return
	
	def recivingPackets(radio_Tx,radio_Rx,windowWindow,slidingWindowsLength,time_ack):
		listLength, listMax, slidingWindowsLength, numberOfPackets = handshakeF(radio_Tx,radio_Rx,time_ack)
		
		radio_Rx.startListening()
		suma = 0
		numWindows=0

		pending=list(range(numberOfPackets))
		recived = {}
		preRecived = {}
		ackPacket=[]
		ackPacketPrev=[]
		numInQueue=0
		global myQueue
		print("On the way to win")
		thread = Thread(target = decodingOnTheGo, args = (listMax))
		thread.start()
		thread2 = Thread(target = decompresionOnTheGo, args = (listMax))
		thread2.start()
		while (1):
				if radio_Rx.available(0):					
					radio_Rx.read(frame, radio_Rx.getDynamicPayloadSize())
					if (frame[0]==254):
						listLength, listMax, slidingWindowsLength, numberOfPackets = handshakeF(radio_Tx,radio_Rx,time_ack)
					flag=pending[frame[0]-numWindows*slidingWindowsLength]
					if (flag>0) and (flag<=slidingWindowsLength):
						preRecived[flag] = frame[1:len(frame)]
						break
		while len(recived)<numberOfPackets:
			######revisar este time out##########
			timeout = time.time() + time_ack
			ackPacket=list("ACK")			
			while (1):
				if radio_Rx.available(0):					
					radio_Rx.read(frame, radio_Rx.getDynamicPayloadSize())
					flag=pending[frame[0]-numWindows*slidingWindowsLength]
					if (flag>0) and (flag<slidingWindowsLength):
						preRecived[flag] = frame[0:len(frame)]
					else
						radio_Tx.write(list(ackPacketPrev))
				if(len(recived)==numberOfPackets) or (len(preRecived)==slidingWindowsLength) or (time.time()) > timeout):	
					for c in preRecived:
						flag=pending[c[0]-numWindows*slidingWindowsLength]
						pending.remove(flag)
						ackPacket+=list(flag)
					recived.update(preRecived)				
					radio_Tx.write(list(ackPacket))
					numWindows=(numWindows+1)%windowsWindows
					ackPacketPrev=ackPacket
					ackPacket=[]
					break
			#Ir añadiendo a la queue
			while(1):
				if (recived.has_key(numInQueue):
					myQueue.put(recived[numInQueue])
					numInQueue+=1
				else
					break
	
	def main():		
		#inicializamos raspberry, transivers
		radio_Tx,radio_Rx = init()
		
		#Flag variables
		original_flag_data = 'A'
		flag = ""
		flag_n = 0

		#Packet related variables
		frame = []
		handshake_frame = []
		compressed = []

		#ACK related variables
		time_ack = 0.2
		receivedPacket = 0
		receivedHandshakePacket = 0
		
		#SlidingWindows
		windowWindow=2
		
		#Threads		 
		global myQueue
		global myQueue2
				    
		#We listen for the control packet handshake		
		#listLength, listMax, slidingWindowsLength, numberOfPackets = handshakeF(radio_Tx,radio_Rx,time_ack)

		#print("The number of data packets that will be transmitted: " + str(numberOfPackets))
		#print("Length of list: " + str(listLength))
		#print("maximum value of list: " + str(listMax))
		#bitsMax = int(np.ceil(np.log(listMax+1)/np.log(2)))
		
		#recive packets
		recivingPackets(radio_Tx,radio_Rx,windowWindow,slidingWindowsLength)
		
		myQueue.join()
		myQueue2.join()
		thread.stop()
		thread2.stop()
		final = time.time()
		totalTime = final - start
		print("Total time: " + str(totalTime))

		print("Number of retransmissions = " + str(suma))

	if __name__ == '__main__':
		main()

except KeyboardInterrupt:
	GPIO.output(22,0)
	GPIO.output(23,0)
	GPIO.output(24,0)
	GPIO.cleanup()
