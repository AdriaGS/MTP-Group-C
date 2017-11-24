try:  
    from lib_nrf24 import NRF24
    from math import *
    import time
    import spidev
    import sys
    import os
    import numpy as np
    import RPi.GPIO as GPIO
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
                j = j + 1
            else:
                compde.append(strJoin>>(x-NewLength))
                strJoin = strJoin & (2**(x-NewLength)-1)
                i += 1
                x = x - NewLengthç
        return compde
    def init():
        start = time.time()
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(23, GPIO.OUT)
        GPIO.output(23,1)
        GPIO.setup(22, GPIO.OUT)
        GPIO.output(22, 1)
        GPIO.setup(24, GPIO.OUT)
        GPIO.output(24,1)

        print("Transmitter")
        pipe_Tx = [0xe7, 0xe7, 0xe7, 0xe7, 0xe7]
        pipe_Rx = [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]
        payloadSize = 32
        channel_TX = 90
        channel_RX = 100

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
        radio_Tx.openWritingPipe(pipe_Tx)
        radio_Rx.openReadingPipe(0, pipe_Rx)

        #We print the configuration details of both transceivers
        radio_Tx.printDetails()
        print("*------------------------------------------------------------------------------------------------------------*")
        radio_Rx.printDetails()
        print("*------------------------------------------------------------------------------------------------------------*")
        return (radio_Tx, radio_Rx)      
    def dataPackets(toSend):
        for i in range (0, len(toSend), dataSize):
            if((i+dataSize) < len(toSend)):
                packets.append(toSend[i:i+dataSize])
            else:
                packets.append(toSend[i:])
        return packets
    def handshakeF(packets, radio_Rx, radio_Tx,time_ack):
        n=1
        while (1):
            if(n==1):
                print("Start handshake:")
                ###STEP 1
                print("STEP 1: Waiting SYN")
                radio_Rx.startListening()
                while (1):
                    if radio_Rx.available(0):
                        radio_Rx.read(frame, radio_Rx.getDynamicPayloadSize())
                        print("Something received")
                        #check if it is a handshake
                        if (frame[0]==255):
                            n=2
                            break
            if(n==2):
                print("SYN recived")
                ###STEP 2
                print("STEP 2: Sending ACK")
                #Send ack_Handshake
                radio_Tx.write(char(254)+str(numberofPackets) + str(listLengh) + "," + str(listMax) + str(slidingWindowsLength))
                timeout = time.time() + time_ack
                n=3
            if(n==3):
                ###STEP 3
                print("STEP 2: Waiting ACK")
                while(1):
                    str_Handshakeframe = ""
                    if radio_Rx.available(0):
                        radio_Rx.read(frame, radio_Rx.getDynamicPayloadSize())
                        print("Something received")
                        #check if it is a handshake
                        if (frame[0]==253):
                            print("ACK received")
                            print("HANDSHAKE DONE")
                            return (listLength, listMax, slidingWindowsLength, numberOfPackets)        
                        elif (frame[0]==255):
                            n=2
                            break
                    elif((time.time()) > timeout):
                        print("TIMEOUT")
                        n=2
                        break   
    def sendingPackets(packets,windowsWindows,timeout,radio_Rx, radio_Tx):
        suma = 0
        messageSended = 0
        pending=list(range(len(packets)))
        numWindows=0
        
        while messageSended<numberofPackets:            
            for x in range(0, min(slidingWindowsLength,len(pending))):                
                flag = chr(ord(numWindows*slidingWindowsLength) + pending(x))
                message2Send = list(flag) + list(packets(x))
                radio_Tx.write(message2Send)
                
            #MIRAR TIEMPOS
            #
            #MIRAR TIEMPOS
            timeout = time.time() + time_ack
            radio_Rx.startListening()
            str_ack = ""
            
            #While we don't receive a correct ack for the transmitted packet we keep trying for the same packet
            while (1):
                if radio_Rx.available(0):
                    radio_Rx.read(ack, radio_Rx.getDynamicPayloadSize())
                    
                    for c in range(0,2):
                        str_ack = str_ack + chr(ack[c])
                    
                    if (list(str_ack)!=(list("ACK"))):
                        print("Waiting ACK but wrong packet arrived")
                    else:
                        for c in range(3, len(ack)):                                
                            pending.remove(ack[c])
                            messageSended+=1                                    
                        #ACK has been received
                        numWindows=(numWindows+1)%windowsWindows
                        break    
                #If an established time passes and we have not received anything we retransmit the data packet
                if((time.time()) > timeout):
                    #print("No Data ACK received resending message")
                    suma += 1
                    break     
    def main():        

        radio_Tx, radio_Rx = init()
        
        #Read file to transmit
        inFile = open("MTP_Prev.txt", "rb")
        data2Tx = inFile.read()
        inFile.close()

        #flag variables
        original_flag = 'A'
        flag = ""
        ctrl_flag_n = 0
        flag_n = 0
        
        #slindingWindows variables
        slidingWindowsLength = 1
        windowsWindows=2 
        
        #packet realted variables
        overhead = 1 # Number of bytes
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

        #Time variables
        time_ack = 0.2

        start_c = time.time()
        
        #Compression of the data to transmit into data2Tx_compressed
        data2Tx_compressed = compress(data2Tx)

        #Compression Preprocessing
        listMax = max(data2Tx_compressed)
        bitsMax = int(np.ceil(np.log(listMax+1)/np.log(2)))
        charLength = 8
        toSend = length_OToN(data2Tx_compressed, charLength, bitsMax)

        final_c = time.time()
        print("Compression time: " + str(final_c-start_c))

        #Now we conform all the data packets in a list
        packets=dataPackets(toSend)
        numberofPackets=len(packets)

        #Start sendind
        #While we don't receive the handshake ack we keep trying
        handshakeF(numberofPackets, listLengh, listMax, slidingWindowsLength, time_ack, radio_Rx, radio_Tx)

        #We iterate over every packet to be sent
        sendingPackets(packets,windowsWindows,timeout,radio_Rx, radio_Tx)
                        
        final = time.time()
        totalTime = final - start
        print(totalTime)
        #print(messageSent == toSend)
        print("Total retransmissions: " + str(suma))

    if __name__ == '__main__':
        main()
        
except KeyboardInterrupt:
    GPIO.output(22,0)
    GPIO.output(23,0)
    GPIO.output(24,0)
    GPIO.cleanup()
