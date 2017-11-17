import sys
import os.path
import numpy as np


def compress(uncompressed):
    """Compress a string to a list of output symbols."""
 
    # Build the dictionary.
    dict_size = 256
    # in Python 2: dictionary = dict((chr(i), i) for i in xrange(dict_size))
    dictionary = {chr(i): i for i in range(dict_size)}
 
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
    # in Python 2: dictionary = dict((i, chr(i)) for i in xrange(dict_size))
    dictionary = {i: chr(i) for i in range(dict_size)}
 
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

def printError(num):
	"""
	printError() prints an error and usage message.

	@params: integer to customize the error message (1 if in decompress(),
			 2 if in compress(), anything else for other).
	@return: n/a.
	"""
	if num == 1:
		print('Error. Invalid compressed list given to decompress().')
	elif num == 2:
		print('Error. Invalid string given to compress().')
	else:
		print('Error.')
	print('Usage:')
	print('Compression: $ lzw.py <something>.txt <something>.lzw compress')
	print('Decompression: $ lzw.py <something>.txt <something>.lzw decompress')
	sys.exit()

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
	#OpenFile
	file='or/test.txt'
	f = open(file,'rb')
	comp = compress(f.read())
	#print("comp= "+str(comp))
	f.close()
	
	#CodingChar
	listLength=len(comp)
	listMax=max(comp)
	bitsMax= int(np.ceil(np.log(listMax+1)/np.log(2)))
	charLength = 8
	comp.append(0)

	remainded = bitsMax
	pad=bitsMax-charLength
	
	string=""
	i=0

	while i < listLength :
	  compJoin = (comp[i]<<bitsMax)+comp[i+1]
	  #print("compJoin= "+str(bin(compJoin)))
	  string += chr((compJoin>>(pad+remainded))%(2**charLength))
	  #print("addString= "+str(bin((compJoin>>(pad+remainded))%(2**charLength))))
	  remainded = remainded - charLength
	  if remainded <=0:
		i=i+1
		remainded= remainded %bitsMax
		if remainded == 0:
		  remainded=bitsMax
	#print("string= "+string)
	
	#Guardar Compress
	f_comp = open('co/testCompress.txt', 'w')
	f_comp.write(string)
	f_comp.close()
	
	#DecodingChar
	i=0
	string+=chr(0)
	strJoin=0
	compde=[]
	x=0
	j=0;


	while i < listLength :
	  if x<bitsMax:
		strJoin=(strJoin<<charLength)+ord(string[j])
		#print("strJoin= "+str(bin(strJoin)))
		x=x+charLength
		j=j+1;
	  else:
		compde.append(strJoin>>(x-bitsMax))
		strJoin=strJoin&(2**(x-bitsMax)-1)
		#print("strJoin2= "+str(bin(strJoin)))
		i=i+1
		x=x-bitsMax

	#print("compde= "+str(compde))

    #Decompress
	decompressed = decompress(compde)
	#Write file
	f = open('dec/testDecompress.txt','w')
	f.write(decompressed)
	f.close()
	
	#Summary
	printSummary(file, 'co/testCompress.txt')
if __name__ == '__main__':
	main()
