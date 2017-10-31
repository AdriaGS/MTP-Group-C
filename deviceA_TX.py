try:

    import RPi.GPIO as GPIO
    from lib_nrf24 import NRF24
    from math import *
    import time
    import spidev

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(23, GPIO.OUT)
    GPIO.output(23,1)
    GPIO.setup(22, GPIO.OUT)
    GPIO.output(22, 1)

    print("Transmitter")
    pipe_Tx = [0xe7, 0xe7, 0xe7, 0xe7, 0xe7]
    pipe_Rx = [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]
    payloadSize = 32
    channel_TX = 0x60
    channel_RX = 0x60

    #Initializa the radio transceivers with the CE ping connected to the GPIO22 and GPIO24
    radio_Tx = NRF24(GPIO, spidev.SpiDev())
    radio_Rx = NRF24(GPIO, spidev.SpiDev())
    radio_Tx.begin(0, 22)
    radio_Rx.begin(0, 24)

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

   	#We print the configuration details of both transceivers
    radio_Tx.printDetails()
    print("*------------------------------------------------------------------------------------------------------------*")
    radio_Rx.printDetails()
    print("*------------------------------------------------------------------------------------------------------------*")

    original_flag = 'A'
    flag = ''
    flag_n = 0
    overhead = 0
    time_ack = 1
    ack = []
    str_ack = ""
    ack_received = 0
    inFile = open("QuickModeFile.txt", "rb")
    data2Tx = inFile.read()
    inFile.close()
    packets = []

    dataSize = payloadSize - overhead
    #Now we conform all the packets in a list
    for i in range (0, len(data2Tx), dataSize):
    	if((i+dataSize) < len(data2Tx)):
    		packets.append(data2Tx[i:i+dataSize])
    	else:
    		packets.append(data2Tx[i:])

    #Start time
    start = time.time()
    #We iterate over every packet to be sent
    for message in packets:
        retransmisions = 0
        flag = chr(ord(original_flag) + flag_n)
    	radio_Tx.write(list(flag) + message)
		time.sleep(1)
    	print("Message sent, waiting ACK: {}".format(message))
    	timeout = time.time() + time_ack
#    	while not (ack_received):
#    		radio_Rx.openReadingPipe(1, pipe_Rx)
#    		radio_Rx.startListening()
#    		if radio_Rx.available(0):
#    			radio_Rx.read(ack, radio_Rx.getDynamicPayloadSize())
#    			for c in range(0, len(ack)):
#    				str_ack = str_ack + chr(ack[c])
#    			print("ACK received: " + str_ack)
#    			if(list(str_ack) != (list("ACK") + list(flag))):
#    				print(list("ACK") + list(flag))
#    				radio_Tx.write(list(flag) + message)
#    				timeout = time.time() + time_ack
#    				print("Message Lost")
#    			else:
#    				ack_received = 1
#    		if((time.time() + 0.01) > timeout):
#			print("No ACK received resending message")
#    			retransmisions += 1
#    			print("Number of retransmision for message " + flag + " = " + str(retransmisions))
#    			radio_Tx.openWritingPipe(pipe_Tx)
#    			radio_Tx.write(list(flag) + message)
#    			timeout = time.time() + time_ack
    	flag_n = (flag_n + 1) % 10

    final = time.time()
    totalTime = final - start
    print(totalTime)
        
except KeyboardInterrupt:
    GPIO.output(23,0)
    GPIO.output(24,0)
    GPIO.cleanup()
	

