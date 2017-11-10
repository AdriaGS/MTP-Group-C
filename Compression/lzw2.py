import sys
import argparse
import pickle
import math

ASCII_SIZE = 256

parser = argparse.ArgumentParser(description='A compression script using the lzw algorithm')
parser.add_argument('-d', '--decompress', help='Decompress output produced by this program', action='store_true')
parser.add_argument('-c', '--compress', help='Compress a string or a file', action='store_true')
parser.add_argument('source', metavar='S', type=str, nargs='?', help='input to compress or decompress')

def encode(s):
	# Produce dict keyed by ascii characters with appropriate index value
	dictionary = dict((chr(c), c) for c in range(ASCII_SIZE))
	max_index = ASCII_SIZE
	resultant_code = []
	current_run = ""
	for c in s:
		# Set our run to the letter in the string + our current run
		run = c + current_run
		# Case when we already have this in our dict (can be compressed further)
		if run in dictionary:
			current_run = run
		else:
			# Update dict and result, reset current run to our current character
			dictionary[run] = max_index
			resultant_code.append(dictionary[current_run])
			max_index += 1
			current_run = c

	# Check last run to see if it needs to be added to result
	if len(current_run) > 0:
		resultant_code.append(dictionary[current_run])
	
	with open('output.dat', 'wb') as f:
		pickle.dump(resultant_code, f, pickle.HIGHEST_PROTOCOL)

def decode(l):
	# Reverse dictionary
	dictionary = dict((c, chr(c)) for c in range(ASCII_SIZE))
	max_index = ASCII_SIZE
	# Add our first entry and set our run
	s = dictionary[l[0]]
	r = s
	for n in l[1:]:
		# Number doesn't exist, we add our current run to first elem
		if n not in dictionary:
			entry = s + s[0]
		else:
			entry = dictionary[n] 
		r += entry
		dictionary[max_index] = s + entry[0]
		max_index += 1
		s = entry

	return r


def main():

		file='ElQuijote.txt'
		f = open(file,'r')
		res = encode(f.read())

		# args = vars(parser.parse_args())
		# if args['decompress']:
		# 		with open(args['source'], 'rb') as f:
		# 			result = pickle.load(f)
		# 		print(decode(result))
		# else:
		# 		res = encode(args['source'])

if __name__ == '__main__':
	main()