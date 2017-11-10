import io
import sys
import os.path
import numpy
import pickle
import sqlite3
import csv
import scipy.io
import mat4py as m4p
import hashlib

def compress(uncompressed):
    """Compress a string to a list of output symbols."""
 
    # Build the dictionary.
    dict_size = 256
    dictionary = {chr(i): i for i in range(dict_size)}
    # dictionary = dict((chr(i), i) for i in xrange(dict_size))
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
 
    # Build the dictionary.
    dict_size = 256
    dictionary = {i: chr(i) for i in range(dict_size)}
    # dictionary = dict((i, chr(i)) for i in xrange(dict_size))
    # in Python 3: dictionary = {i: chr(i) for i in range(dict_size)}
 
    # use StringIO, otherwise this becomes O(N^2)
    # due to string concatenation in a loop
    result = io.StringIO()
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
 
 
def md5Checksum(filePath):
    with open(filePath, 'rb') as fh:
        m = hashlib.md5()
        while True:
            data = fh.read(8192)
            if not data:
                break
            m.update(data)
        return m.hexdigest()

# How to use:
file='RXFILE-D-SRI-1.txt'
f = open(file,'r')
compressed = compress(f.read())
f.close()

f_comp = open('co/testCompress3.dat','wb')
for i in compressed:
    single_byte = i.to_bytes(2, byteorder='big', signed=True)
    f_comp.write(single_byte)

f_comp.close()

decompressed = decompress(compressed)

f = open('dec/testDecompress3.txt','w')
f.write(decompressed)
f.close()

print(md5Checksum('RXFILE-D-SRI-1.txt') == md5Checksum('dec/testDecompress3.txt'))