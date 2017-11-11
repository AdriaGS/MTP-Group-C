import lzw

infile = lzw.readbytes("ElQuijote.txt")
compressed = lzw.compress(infile)
lzw.writebytes("My Compressed File.lzw", compressed)

print(type(compressed))
print(str(compressed))

infile = lzw.readbytes("My Compressed File.lzw", compressed)
uncompressed = lzw.decompress(infile)