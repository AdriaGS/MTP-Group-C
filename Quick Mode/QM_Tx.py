try:

    import RPi.GPIO as GPIO
    from lib_nrf24 import NRF24
    import time
    import spidev

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(23, GPIO.OUT)
    GPIO.output(23,1)
    GPIO.setup(22, GPIO.OUT)
    GPIO.output(22,1)
    
    print("Transmitter")
    pipes = [0xe7, 0xe7, 0xe7, 0xe7, 0xe7]

    radio = NRF24(GPIO, spidev.SpiDev())
    radio.begin(1, 22)
    radio.setPayloadSize(1)
    radio.setChannel(63)

    radio.setDataRate(NRF24.BR_2MBPS)
    radio.setPALevel(NRF24.PA_HIGH)
    radio.setAutoAck(False)
    radio.enableDynamicPayloads()

    radio.openWritingPipe(pipes)
    radio.printDetails()
    print("///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////")

    i = 0

    while True:
        #print("Transmitting Ping")
        message = 0xFF
        radio.write(str(message))
        #time.sleep(1)
        i += 1
        
except KeyboardInterrupt:

    radio.write("HE XAPAT")
    GPIO.output(22,0)
    GPIO.output(23,0)
    #GPIO.output(24,0)
    GPIO.cleanup()
