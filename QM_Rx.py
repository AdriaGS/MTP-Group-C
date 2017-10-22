try:

    import RPi.GPIO as GPIO
    from lib_nrf24 import NRF24
    import time
    import spidev

    GPIO.setmode(GPIO.BCM)
    #GPIO.setup(23, GPIO.OUT)
    #GPIO.output(23,1)
    
    print("Transmitter")
    pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]

    radio = NRF24(GPIO, spidev.SpiDev())
    radio.begin(0, 22)
    radio.setPayloadSize(32)
    radio.setChannel(0x60)

    radio.setDataRate(NRF24.BR_250KBPS)#2MBPS)
    radio.setPALevel(NRF24.PA_MAX)#MIN)
    radio.setAutoAck(False)
    radio.enableDynamicPayloads()

    radio.openReadingPipe(0, pipes[1])
    radio.printDetails()
    print("///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////")

    frame = []

    print("Waiting Ping")

    while True:
        radio.startListening()
        if radio.available(0):
            radio.read(frame, radio.getDynamicPayloadSize())
            pritn("Received Message: ")
            print(frame)
        
except KeyboardInterrupt:
    GPIO.output(23,0)
    GPIO.output(24,0)
    GPIO.cleanup()
