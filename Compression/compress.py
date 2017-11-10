import sys
import os.path
import numpy
import pickle
import sqlite3
import csv
import scipy.io
import mat4py as m4p
import bitarray

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
	file='ElQuijote.txt'
	f = open(file,'r')
	comp = compress(f.read())
	f.close()

	print(type(comp))

	str1 = ''.join(bin(e) for e in comp)

	f1 = open('testCompressed.dat', 'wb')
	f1.write(str1)
	f1.close()
	
	#print(comp)
	
	#save
	f_comp = open('co/testCompress.txt','wb')
	pickle.dump(comp,f_comp)
	f_comp.close()
	
	f_comp = open('co/testCompress.np','wb')
	numpy.save(f_comp,comp)
	f_comp.close()
	
	f_comp = csv.writer(open("co/testCompress.csv", "w"))
	f_comp.writerow(comp)
	
	m4p.savemat('co/testCompress.mat', {'dic':comp})

	
	printSummary(file, 'co/testCompress.txt')

if __name__ == '__main__':
	main()