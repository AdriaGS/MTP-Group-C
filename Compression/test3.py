import sys
import os.path
import numpy
import pickle
import sqlite3
import csv
import scipy.io
import mat4py as m4p
import array
from bitarray import bitarray
import time
import lzw

def compress(uncompressed):
	"""Compress a string to a list of output symbols."""
 
	# Build the dictionary.
	dict_size = 256
	dictionary = {chr(i): i for i in range(dict_size)}
	#dictionary = dict((chr(i), i) for i in xrange(dict_size))
	# in Python 3: dictionary = {chr(i): i for i in range(dict_size)}
 
	w = ""
	result = []
	for c in uncompressed:
		wc = w + c
		if wc in dictionary:
			w = wc
		else:
			result.append(dictionary[w])
			# Add wc to the dictionary.
			dictionary[wc] = dict_size
			dict_size += 1
			w = c
 
	# Output the code for w.
	if w:
		result.append(dictionary[w])
	return result

def decompress(compressed):
	"""Decompress a list of output ks to a string."""
	from cStringIO import StringIO
 
	# Build the dictionary.
	dict_size = 256
	dictionary = dict((i, chr(i)) for i in xrange(dict_size))
	# in Python 3: dictionary = {i: chr(i) for i in range(dict_size)}
 
	# use StringIO, otherwise this becomes O(N^2)
	# due to string concatenation in a loop
	result = StringIO()
	w = chr(compressed.pop(0))
	result.write(w)
	for k in compressed:
		if k in dictionary:
			entry = dictionary[k]
		elif k == dict_size:
			entry = w + w[0]
		else:
			raise ValueError('Bad compressed k: %s' % k)
		result.write(entry)
 
		# Add w+entry[0] to the dictionary.
		dictionary[dict_size] = w + entry[0]
		dict_size += 1
 
		w = entry
	return result.getvalue()

def printSummary(file1, file2):
	"""
	printSummary() prints out the number of bytes in the original file and in
	the result file.

	@params: two files that are to be checked.
	@return: n/a.
	"""
	# Checks if the files exist in the current directory.
	if (not os.path.isfile(file1)) or (not os.path.isfile(file2)):
		printError(0)

	# Finds out how many bytes in each file.
	f1_bytes = os.path.getsize(file1)
	f2_bytes = os.path.getsize(file2)

	sys.stderr.write(str(file1) + ': ' + str(f1_bytes) + ' bytes\n')
	sys.stderr.write(str(file2) + ': ' + str(f2_bytes) + ' bytes\n')

def main():	

	dataSize = 32
	file='SampletextFile1Mb.txt'
	f = open(file,'rb')
	data2Tx = f.read()
	f.close()

	start_c = time.time()
	#Compression of the data to transmit into data2Tx_compressed
	data2Tx_compressed = compress(data2Tx)
	n=len(bin(max(data2Tx_compressed)))-2

	#We create the string with the packets needed to decompress the file transmitted
	controlList_extended = []
	controlList = []
	
	for val in data2Tx_compressed:
		division = int(val/256)
		controlList.append(division)

	if(n > 16):
		for val in controlList:
			division = int(val/256)
			controlList_extended.append(division)

	for y in range(0, len(data2Tx_compressed)):
		data2Tx_compressed[y] = data2Tx_compressed[y] % 256
	for x in range(0, len(controlList)):
		controlList[x] = controlList[x] % 256


	data2Send = []
	for iterator in range(0, len(controlList)):
		data2Send.append(data2Tx_compressed[iterator])
		data2Send.append(controlList[iterator])
		if(n > 16):
			data2Send.append(controlList_extended[iterator])

	final_c = time.time()
	print("Compression time: " + str(final_c-start_c))

	start_d = time.time()

	indexing_0 = range(0, len(data2Send), int(n/8.5)+1)[0:]
	indexing_1 = range(1, len(data2Send), int(n/8.5)+1)[0:]
	if(n > 16):
		indexing_2 = range(2, len(data2Send), 3)[0:]

	compressed = [data2Send[i] for i in indexing_0]
	multData = [data2Send[i] for i in indexing_1]
	if(n > 16):
		multData_extended = [data2Send[i] for i in indexing_2]

	compressed = list(map(int, compressed))
	multData = list(map(int, multData))
	if(n > 16):
		multData_extended = list(map(int, multData_extended))

	outputFile = open("ReceivedFileCompressed1.txt", "wb")

	if(n > 16):
		multData_extended = [ik * 256 for ik in multData_extended]
		multData = [sum(xk) for xk in zip(multData, multData_extended)]

	new_mulData = [il * 256 for il in multData]
	toDecompress = [sum(x) for x in zip(compressed, new_mulData)]

	str_decompressed = decompress(toDecompress)
	outputFile.write(str_decompressed)
	outputFile.close()

	final_d = time.time()
	print("Decompression time: " + str(final_d-start_d))

if __name__ == '__main__':
	main()