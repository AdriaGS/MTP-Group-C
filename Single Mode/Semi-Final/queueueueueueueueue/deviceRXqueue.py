try:
    import RPi.GPIO as GPIO
    from lib_nrf24 import NRF24
    import time
    import spidev
    import numpy as np
    from threading import Thread
    from multiprocessing import Queue as queue

    myQueue = queue.Queue()
    myQueue2 = queue.Queue()

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
        OriginalLength=8
        
        while (1):
            if x < NewLength:
                strJoin = (strJoin<<OriginalLength) + ord(myQueue.get())
                x = x + OriginalLength
                j = j + 1
            else:
                myQueue2.put(strJoin>>(x-NewLength))
                strJoin = strJoin & (2**(x-NewLength)-1)
                i += 1
                x = x - NewLength
            myQueue.task_done()

    def decompresionOnTheGo    (listMax,outputFile):    
        ##Mirar si hay conflicots con windows o donde sea por no usar binario.
        
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
            # Add w+entry[0] to the dictionary.
            dictionary[dict_size] = w + entry[0]
            dict_size += 1
            w = entry
            myQueue2.task_done()

    def init() :
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
        channel_RX = 40
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
        #radio_Tx.setDataRate(NRF24.BR_250KBPS)
        #radio_Rx.setDataRate(NRF24.BR_250KBPS)
        radio_Tx.setDataRate(NRF24.BR_2MBPS)
        radio_Rx.setDataRate(NRF24.BR_2MBPS)

        #Configuration of the power level to be used by the transceiver
        radio_Tx.setPALevel(NRF24.PA_LOW)
        radio_Rx.setPALevel(NRF24.PA_LOW)

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

        #We print the configuration details of both transceivers
        radio_Tx.printDetails()
        print("*------------------------------------------------------------------------------------------------------------*")
        radio_Rx.printDetails()
        print("*------------------------------------------------------------------------------------------------------------*")
    
    def main():        
        
        radio_Tx,radio_Rx = init()
        
        #Flag variables
        original_flag_data = 'A'
        flag = ""
        flag_n = 0
        ctrl_flag_n = 0

        #Packet related variables
        frame = []
        handshake_frame = []

        #ACK related variables
        time_ack = 0.1
        receivedPacket = 0
        receivedHandshakePacket = 0

        #Queue
        global myQueue
        global myQueue2
        #Open file
        outputFile = open("RxFile-MTPGroupC.txt", "wb")
        #starting threads
        thread = Thread(target = decodingOnTheGo, args = (listMax))
        thread.start()
        thread2 = Thread(target = decompresionOnTheGo, args = (listMax, outputFile))
        thread2.start()

        ###############################################################################################################################
        ###############################################################################################################################
        ###############################################################################################################################
            
        #We listen for the control packet
        radio_Rx.startListening()
        while not (receivedHandshakePacket):
            str_Handshakeframe = ""

            if radio_Rx.available(0):
                radio_Rx.read(handshake_frame, radio_Rx.getDynamicPayloadSize())
                print("Something received")

                for c in range(0, len(handshake_frame)):
                    str_Handshakeframe = str_Handshakeframe + chr(handshake_frame[c])

                #print("Handshake frame: " + str_Controlframe)
                if(len(str_Handshakeframe.split(",")) == 4):
                    print("Sending ACK")
                    radio_Tx.write(list("ACK"))
                    checksum, numberOfPackets, listLength, listMax = str_Handshakeframe.split(",")
                    listLength = int(listLength)
                    listMax = int(listMax)
                
                else:
                    if(chr(handshake_frame[0]) == original_flag_data):
                        print("First data packet received")
                        handshake_frame = handshake_frame[1:len(handshake_frame)]
                        for char in handshake_frame :
                            myQueue.put(char)

                        radio_Tx.write(list("ACK") + list(original_flag_data))
                        flag_n = (flag_n + 1) % 10
                        receivedHandshakePacket = 1

        print("The number of data packets that will be transmitted: " + numberOfPackets)
        print("Length of list: " + str(listLength))
        print("maximum value of list: " + str(listMax))
        bitsMax = int(np.ceil(np.log(listMax+1)/np.log(2)))

        ###############################################################################################################################
        ###############################################################################################################################
        ###############################################################################################################################

        radio_Rx.startListening()
        suma = 0

        for i in range(0, int(numberOfPackets)-1):

            timeout = time.time() + time_ack
            flag = chr(ord(original_flag_data) + flag_n)

            while not (receivedPacket):

                if radio_Rx.available(0):
                    radio_Rx.read(frame, radio_Rx.getDynamicPayloadSize())
                    #print(frame)

                    if(chr(frame[0]) == flag):
                        for char in frame[1:len(frame)]:
                            myQueue.put(char)
                        radio_Tx.write(list("ACK") + list(flag))
                        receivedPacket = 1
                    else:
                        if ((suma % 10) == 0):
                            print("Number of retransmissions increasing: " + str(suma))
                        suma += 1
                        if flag_n == 0:
                            radio_Tx.write(list("ACK") + list('J'))
                        else:
                            radio_Tx.write(list("ACK") + list(chr(ord(original_flag_data) + flag_n-1)))
                        timeout = time.time() + time_ack

            flag_n = (flag_n + 1) % 10
            receivedPacket = 0


        myQueue.join()      
        thread.stop()
        myQueue2.join()        
        thread2.stop()
        outputFile.close()

        ###############################################################################################################################
        ###############################################################################################################################
        ###############################################################################################################################

        #Compute Cksum
        textFile = "RxFile-MTPGroupC.txt"
        command = "cksum " + textFile + " > checksum.txt"
        os.system(command)
        checksumFile = open("checksum.txt", 'rb')
        checksumRx = checksumFile.read()
        print(checksumRx)

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
