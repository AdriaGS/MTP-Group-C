import RPi.GPIO as GPIO
import time

def led_blink(gpio_value, stop_event):

	while(not stop_event.is_set()):
		GPIO.output(gpio_value, 1)
		time.sleep(0.5)
		GPIO.output(gpio_value, 0)
		time.sleep(0.5)


GPIO.setmode(GPIO.BCM)
GPIO.setup(2, GPIO.OUT, GPIO.LOW) #LED 1 TX_RX Running
GPIO.setup(3, GPIO.OUT, GPIO.LOW) #LED 2 End-of-File
GPIO.setup(14, GPIO.IN) #ON or OFF
GPIO.setup(15, GPIO.IN) #Transmit or Receive
GPIO.setup(18, GPIO.IN) #Network Mode

TX0_RX1 = True

while True:
	input_onoff = GPIO.input(14)
	input_tx_rx = GPIO.input(15)
	input_nm = GPIO.input(18)

	#LED Blinking thread
	led_1 = Event()
	led_thread = Thread(target = led_blink, args = (2, led_1))

	if(input_onoff == True):
		time.sleep(1)
		print("Waiting to start")
		print("Tx=1 or Rx=0: " + str(input_tx_rx))
		print("Network Mode: " + str(input_nm))

		led_thread.start()

	else:
		time.sleep(1)
		print("Starting Script")
		print("Tx=1 or Rx=0: " + str(input_tx_rx))
		print("Network Mode: " + str(input_nm))

		led_1.set()