import os
import sys

os.system("cksum ElQuijote.txt > checksum.txt")

infile = open("checksum.txt", 'rb')
f = infile.read()

print(f[0:15])

print("hola" == "hola")


for i in range(0, 10):

	if i == 5:
		print("Reseting...")
		os.execv(sys.executable, ['python'] + sys.argv)