try:

    import RPi.GPIO as GPIO
    from lib_nrf24 import NRF24
    import time
    import spidev

    GPIO.setmode(GPIO.BCM)
    
    print("Transmitter")
    pipes = [0xe7, 0xe7, 0xe7, 0xe7, 0xe7]

    radio = NRF24(GPIO, spidev.SpiDev())
    radio.begin(1, 22)
    radio.setPayloadSize(32)
    radio.setChannel(20)

    radio.setDataRate(NRF24.BR_250KBPS)#2MBPS)
    radio.setPALevel(NRF24.PA_HIGH)
    radio.setAutoAck(False)
    radio.enableDynamicPayloads()

    radio.openWritingPipe(pipes)
    radio.printDetails()
    print("///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////")

    i = 0

    while True:
        #print("Transmitting Ping")
        message = "PINGDEPROBAMTPGROUPC " + str(i)
        radio.write(list(message))
        #time.sleep(1)
        i += 1
        
except KeyboardInterrupt:

    radio.write("HE XAPAT")
    #GPIO.output(22,0)
    GPIO.output(23,0)
    #GPIO.output(24,0)
    GPIO.cleanup()
