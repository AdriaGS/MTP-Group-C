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

	finalData = ""
	midData = ""
	file='ElQuijote.txt'
	f = open(file,'rb')
	comp = compress(f.read())
	f.close()

	n=len(bin(max(comp)))-2
	num=2**(n+1)
	enviar = []

	aux = []
	aux2 = []
	binary = lambda n: n>0 and [n&1]+binary(n>>1) or []

	for a in comp:
		aux2=binary(a|num)
		del aux2[-1]
		aux += aux2[::-1]
	#print ("B"+str(aux))


	i=0
	while i < len(aux):
	  r=aux[i:i+7]
	  char=0
	  for p in r:
		char=char<<1
		char=char|p
	  enviar.append(char)
	  i+=8


	print(len(enviar))


	


	for x in comp:
		midData += str(x)

	print(len(comp))
	print("Max of first compression: " + str(max(comp)))
	print(bin(max(comp)))
	print(len(bin(max(comp))))

	



	#string = "".join(chr(val) for val in comp)

	#print(string)

	#print(bitarray(str1))

	#for i in str1:
		#print(i)

if __name__ == '__main__':
	main()