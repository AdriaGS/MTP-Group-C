import lzw

inFile = open("MTP_Prev.txt", 'rb')

enc = lzw.ByteEncoder(12)
bigstr = inFile.read()
encoding = enc.encodetobytes(bigstr)
encoded = b"".join( b for b in encoding )

outFile = open("Compressed.txt", 'wb')
outFile.write(encoded)

dec = lzw.ByteDecoder()
decoding = dec.decodefrombytes(encoded)
decoded = b"".join(decoding)

print(decoded == bigstr)