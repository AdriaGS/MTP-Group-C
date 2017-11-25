try:
    # Carrier testing mode
    # It outputs a const clean carrier, for testing purposes
    import RPi.GPIO as GPIO
    from lib_nrf24 import NRF24
    import time
    import spidev

    GPIO.setmode(GPIO.BCM)
    #GPIO.setup(23, GPIO.OUT)
    #GPIO.output(23,1)
    GPIO.setup(22, GPIO.OUT)
    GPIO.output(22,0)
    
    print("Constant output carrier mode")

    radio = NRF24(GPIO, spidev.SpiDev())
    radio.powerUp() # sets PWR=1 CONFIG register
    radio.write_register(NRF24.CONFIG, radio.read_register(NRF24.CONFIG) & ~_BV(NRF24.PRIM_RX)) # set PRIM_RX=0 in CONFIG register
    time.sleep(150 / 1000000.0) #wait 150 us
    radio.write_register(NRF24.RF_SETUP,radio.read_register(NRF24.RF_SETUP) | _BV(NRF24.PLL_LOCK)) # set PLL_LOCK=1 in R_SETUP register
    time.sleep(150 / 1000000.0) #wait 150 us
    
    radio.begin(1, 22)
    radio.setPALevel(NRF24.PA_MIN) 
    radio.setChannel(100)
    radio.disableCRC();
    radio.printDetails()
    
    while True
        radio.ce(NRF24.HIGH) # assure ce is high constanly to keep carrier
    
    
        
except KeyboardInterrupt:

    GPIO.output(22,0)
    GPIO.output(23,0)
    #GPIO.output(24,0)
    GPIO.cleanup()