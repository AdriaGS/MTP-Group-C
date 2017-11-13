import lzw
import time


start_c = time.time()
inFile = open("MTP_Prev.txt", 'rb')

enc = lzw.ByteEncoder(12)
bigstr = inFile.read()
encoding = enc.encodetobytes(bigstr)
encoded = b"".join( b for b in encoding )

final_c = time.time()

print(final_c - start_c)

outFile = open("Compressed.txt", 'wb')
outFile.write(encoded)

start_d = time.time()
dec = lzw.ByteDecoder()
decoding = dec.decodefrombytes(encoded)
decoded = b"".join(decoding)

outFile = open("MTP_Prev_received.txt", 'wb')
outFile.write(decoded)
outFile.close()

final_d = time.time()
print(final_d - start_d)

print(decoded == bigstr)