GPIO.setmode(GPIO.BCM)
GPIO.setup(22, GPIO.OUT)
GPIO.setup(23, GPIO.OUT)
GPIO.setup(2, GPIO.OUT) #LED 1 TX_RX Running
GPIO.setup(3, GPIO.OUT) #LED 2 End-of-File
GPIO.setup(14, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #ON or OFF
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #Transmit or Receive
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #Network Mode

GPIO.output(22, 1)
GPIO.output(23, 1)

TX0_RX1 = True

while True:
	input_onoff = GPIO.input(14)
	input_tx_rx = GPIO.input(15)
	input_nm = GPIO.input(18)
	if(input_onoff == True):
		time.sleep(1)
		print("Waiting to start")
		print("Tx or Rx: " + str(input_txrx))
		print("Tx or Rx: " + str(input_nm))
	else:
		TX_RX = input_txrx
		NM = input_nm
		print("Starting Script")
		print("Tx or Rx: " + str(input_txrx))
		print("Tx or Rx: " + str(input_nm))