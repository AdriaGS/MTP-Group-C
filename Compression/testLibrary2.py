import lzw

mybytes = lzw.readbytes("ElQuijote.txt")
lessbytes = lzw.compress(mybytes)

outFile = open("Compressed.txt", 'wb')
outFile.write(b"".join(lessbytes))
outFile.close()

newbytes = b"".join(lzw.decompress(lessbytes))
oldbytes = b"".join(lzw.readbytes("ElQuijote.txt"))

print(oldbytes == newbytes)