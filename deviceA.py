try:

    import RPi.GPIO as GPIO
    from lib_nrf24 import NRF24
    from math import *
    import time
    import spidev

    GPIO.setmode(GPIO.BCM)
    #GPIO.setup(23, GPIO.OUT)
    #GPIO.output(23,1)
    
    print("Transmitter")
    pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]
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
    radio_Tx.setPALevel(NRF24.PA_MAX)
    radio_Rx.setPALevel(NRF24.PA_MAX)

    #We disable the Auto Acknowledgement
    radio_Tx.setAutoAck(False)
    radio_Rx.setAutoAck(False)
    radio_Tx.enableDynamicPayloads()
    radio_Rx.enableDynamicPayloads()

    #Open the writing and reading pipe
    radio_Tx.openWritingPipe(pipes[1])

   	#We print the configuration details of both transceivers
    radio_Tx.printDetails()
    print("*------------------------------------------------------------------------------------------------------------*")
    radio_Rx.printDetails()
    print("*------------------------------------------------------------------------------------------------------------*")

    flag = 0
    overhead = 1
    time_ack = 0.5
    ack = []
    str_ack = ""
    ack_received = 0
    inFile = open("prova1.txt", "rb")
    data2Tx = inFile.read()
    inFile.close()
    packets = []

    dataSize = payloadSize - overhead
    #Now we conform all the packets in a list
    for i in range (0, len(data2Tx), dataSize):
    	if((i+dataSize) < len(data)):
    		packets.append(data[i:i+dataSize])
    	else:
    		packets.append(data[i:])

    #Start time
    start = time.time()
    #We iterate over every packet to be sent
    for message in packets:
    	radio_Tx.write(str(flag) + message)
    	print("Message sent, waiting ACK: {}".format(message))
    	timeout = time.time() + time_ack
    	while(!ack_received):
    		radio_Rx.openReadingPipe(0, pipes[0])
    		radio_Rx.startListening()
    		if radio_Rx.available(0):
    			radio_Rx.read(ack, radio_Rx.getDynamicPayloadSize())
    			for c in range(0, len(ack)):
    				str_ack = str_ack + chr(ack[c])
    			print("ACK received: " + str_ack)
    			if(list(str_ack) != (list("ACK") + list(str(flag)))):
    				print(list("ACK") + list(str(flag)))
    				radio_Tx.write(str(flag) + message)
    				timeout = time.time() + time_ack
    				print("Message Lost")
    			else:
    				ack_received = 1
    		if((time.time() + 0.2) > timeout):
    			print("No ACK received resending message")
    			retransmisions += 1
    			print("Number of retransmision for message " + str(flag) + " = " + str(retransmisions))
    			radio_Tx.openWritingPipe(pipes[1])
    			radio.write(str(flag) + message)
    			timeout = time.time() + time_ack
    	flag += 1 % 10

    final = time.time()
    totalTime = final - start
    print(totalTime)
        
except KeyboardInterrupt:
    GPIO.output(23,0)
    GPIO.output(24,0)
    GPIO.cleanup()
	