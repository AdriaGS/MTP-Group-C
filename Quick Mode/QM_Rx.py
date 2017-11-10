try:

    import RPi.GPIO as GPIO
    from lib_nrf24 import NRF24
    import time
    import spidev

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(22, GPIO.OUT)
    GPIO.output(22,1)
    
    print("Transmitter")
    pipes = [0xe7, 0xe7, 0xe7, 0xe7, 0xe7]

    radio = NRF24(GPIO, spidev.SpiDev())
    radio.begin(0, 22)
    radio.setPayloadSize(32)
    radio.setChannel(0x60)

    radio.setDataRate(NRF24.BR_250KBPS)#2MBPS)
    radio.setPALevel(NRF24.PA_LOW)
    radio.setAutoAck(False)
    radio.enableDynamicPayloads()

    radio.openReadingPipe(1, pipes)
    radio.printDetails()
    print("///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////")

    frame = []

    print("Waiting Ping")

    while True:
        radio.startListening()
        while not radio.available(0):
            time.sleep(1/100)
       	radio.read(frame, radio.getDynamicPayloadSize())
        str_frame = ""
        for c in range(0, len(frame)):
        	str_frame += chr(frame[c])
        print("Received Message: ")
        print(str_frame)
            
except KeyboardInterrupt:
    GPIO.output(22,0)
    #GPIO.output(24,0)
    GPIO.cleanup()
