from struct import pack, unpack

lista = [2,3]
n=17
num=2**(n+1)
enviar = []

aux = []
aux2 = []
binary = lambda n: n>0 and [n&1]+binary(n>>1) or []

for a in lista:
		aux2=binary(a|num)
		del aux2[-1]
		aux += aux2[::-1]
print ("B"+str(aux))

for i in range(0, len(aux), 8):
	r=aux[i:i+8]
	char=0
	for p in r:
		char=char<<1
		char=char|p
	enviar.append(char)

print(enviar)

toDecompress_mid = []
pos = 0
for x in enviar:
	binary = bin(x)
	binary = binary[2:len(binary)]
	bitLength = len(binary)

	if(pos != (len(enviar)-1)):
		for i in range(0, 8-bitLength):
			binary = "0" + binary
	else:
		for i in range(0, (len(lista)*(n+1) - (pos)*8) - bitLength):
			binary = "0" + binary

	toDecompress_mid.extend(list(binary))
	pos += 1

toDecompress_mid = list(map(int, toDecompress_mid))

print(toDecompress_mid)

toDecompress = []
for j in range(0, len(toDecompress_mid), n+1):
	l = toDecompress_mid[j: j+(n+1)]
	value = 0
	for k in range(0, len(l)):
		value += (int(l[k]) * 2**(n-k))
	toDecompress.append(value)

print(toDecompress)