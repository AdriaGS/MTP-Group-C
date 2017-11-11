#!/usr/bin/python
# -*- coding: latin-1 -*-
import random

outputfile = open("MTP_Prev.txt", "w")

for i in range (0, 20000):

	rand = random.randint(0, 10)
	string = str(i) + "\tAvui fa un dia fantàstic MTP-S17\tEquip D SRI-1\t"  + str(rand) + "\t\n"
	outputfile.write(string)

outputfile.close()