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

	start_c = time.time()
	finalData = ""
	midData = ""
	file='MTP_Prev.txt'
	f = open(file,'rb')
	comp = compress(f.read())
	f.close()

	n=len(bin(max(comp)))-2
	num=2**(n+1)
	enviar = []

	aux = []
	aux2 = []

	for a in comp:
		aux2 = lzw.inttobits(a, n+1)
		aux.extend(aux2)

	for i in range(0, len(aux), 8):
		r=aux[i:i+8]
		char=0
		for p in r:
			char=char<<1
			char=char|p
		enviar.append(char)

	final_c = time.time()
	print("Total time compression: " + str(final_c-start_c))

	start_d = time.time()
	toDecompress_mid = []
	pos = 0
	for x in enviar:
		
		if(pos != (len(enviar)-1)):
			binary = lzw.inttobits(x, 8)
		else:
			binary = lzw.inttobits(x, (len(comp)*(n+1) - (pos)*8))
	
		toDecompress_mid.extend(binary)
		pos += 1

	#toDecompress_mid = list(map(int, toDecompress_mid))

	toDecompress = []
	for j in range(0, len(toDecompress_mid), n+1):
		l = toDecompress_mid[j: j+(n+1)]
		value = lzw.intfrombits(l)
		toDecompress.append(value)

	#print(toDecompress)

	str_decompressed = decompress(toDecompress)

	#print("Max of compression: " + str(max(comp)))
	
	outputFile = open("Deco_test3.txt", "wb")
	outputFile.write(str_decompressed)
	outputFile.close()

	final_d = time.time()
	print("Total time decompression: " + str(final_d-start_d))

if __name__ == '__main__':
	main()