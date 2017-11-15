from threading import Thread, Event
import time

def threaded_function(arg, stop_event):
	while(not stop_event.is_set()):
		print "running"
		time.sleep(1)


if __name__ == "__main__":
	t_1 = Event()
	thread = Thread(target = threaded_function, args = (10, t_1))
	thread.start()
	time.sleep(5)
	t_1.set()
	print "thread finished...exiting"