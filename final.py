try:

    import RPi.GPIO as GPIO
    from lib_nrf24 import NRF24
    import time
    import spidev

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(24, GPIO.OUT)
    GPIO.setup(23, GPIO.OUT)
    GPIO.setup(16, GPIO.OUT)#LED 1
    GPIO.setup(20, GPIO.OUT)#LED 2
    GPIO.setup(14, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)#TXRX
    GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)#ONOFF
    GPIO.output(23,1)
    GPIO.output(24,1)
    GPIO.output(16,0)
    GPIO.output(20,0)

    TX_RX=True
    
    while True:
        input_onoff= GPIO.input(15)
        input_txrx= GPIO.input(14)
        if(input_onoff==True):
            time.sleep(1)
            print("waiting")
        else:
            TX_RX=input_txrx
            break
            
        
            
    if(TX_RX):
        print("Transmitter")
        pipes = [[0xe7, 0xe7, 0xe7, 0xe7, 0xe7], [0xc2, 0xc2, 0xc2, 0xc2, 0xc2]]

        radio = NRF24(GPIO, spidev.SpiDev())
        radio.begin(0, 17)
        radio.setPayloadSize(32)
        radio.setChannel(0x60)  # this is the lower channel

        radio.setDataRate(NRF24.BR_250KBPS)#2MBPS)
        radio.setPALevel(NRF24.PA_HIGH)#MIN)
        radio.setAutoAck(False)
        radio.enableDynamicPayloads()
    ##    radio.enableAckPayload()

        # radio.openReadingPipe(1, pipes[1])
        radio.openWritingPipe(pipes[1])
        radio.printDetails()
        print("///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////")

        while True:
            radio.write("PING")
            time.sleep(1)
        
except KeyboardInterrupt:
    GPIO.output(23,0)
    GPIO.output(24,0)
    GPIO.cleanup()
