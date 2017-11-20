try:

    import RPi.GPIO as GPIO
    from lib_nrf24 import NRF24
    import time
    import spidev

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(23, GPIO.OUT)
    GPIO.output(23, 1)
    
    print("Transmitter")
    pipes = [0xe7, 0xe7, 0xe7, 0xe7, 0xe7]

    radio = NRF24(GPIO, spidev.SpiDev())
    radio.begin(0, 23)
    radio.setPayloadSize(32)
    radio.setChannel(0x20)

    radio.setDataRate(NRF24.BR_250KBPS)#2MBPS)
    radio.setPALevel(NRF24.PA_MIN)
    radio.setAutoAck(False)
    radio.enableDynamicPayloads()

    radio.openWritingPipe(pipes)
    radio.printDetails()
    print("///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////")

    while True:
        print("Transmitting Ping")
        message = list("PINGDEPRUEBAMTPPROJECTTEAMC")
        radio.write(message)
        time.sleep(1)
        
except KeyboardInterrupt:
    GPIO.output(22,0)
    GPIO.output(23,0)
    GPIO.output(24,0)
    GPIO.cleanup()
