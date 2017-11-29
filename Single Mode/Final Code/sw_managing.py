import RPi.GPIO as GPIO
import time
from threading import Thread, Event

def led_blink(gpio_value, stop_event):

	global blink
	while(blink):
		GPIO.output(gpio_value, 1)
		time.sleep(0.5)
		GPIO.output(gpio_value, 0)
		time.sleep(0.5)


GPIO.setmode(GPIO.BCM)
GPIO.setup(2, GPIO.OUT) #LED 1 TX_RX Running
GPIO.setup(3, GPIO.OUT) #LED 2 End-of-File
GPIO.setup(14, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #ON or OFF
GPIO.setup(15, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #Transmit or Receive
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #Network Mode

GPIO.output(2, 0)
GPIO.output(3, 0)

TX0_RX1 = True

while True:
	input_onoff = GPIO.input(14)
	input_tx_rx = GPIO.input(15)
	input_nm = GPIO.input(18)
	global blink
	blink = 1

	#LED Blinking thread
	led_1 = Event()
	led_thread = Thread(target = led_blink, args = (2, led_1))

	if(input_onoff == True):
		time.sleep(1)
		print("Waiting to start")
		print("Tx=1 or Rx=0: " + str(input_tx_rx))
		print("Network Mode: " + str(input_nm))


		#GPIO.output(2, 0)
		GPIO.output(3, 0)
		led_thread.start()


	else:
		time.sleep(1)
		print("Starting Script")
		print("Tx=1 or Rx=0: " + str(input_tx_rx))
		print("Network Mode: " + str(input_nm))

		blink = 0
		led_thread.join()
		GPIO.output(3, 1)

