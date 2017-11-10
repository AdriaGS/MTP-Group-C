import lzw

infile = lzw.readbytes("My Uncompressed File.txt")
compressed = lzw.compress(infile)
lzw.writebytes("My Compressed File.lzw", compressed)