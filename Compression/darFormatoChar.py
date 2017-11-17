import numpy as np

comp = [255,257,1231,6484,8484,5484849,8484,1]

listLengh=len(comp)
listMax=max(comp)
bitsMax= int(np.ceil(np.log(listMax+1)/np.log(2)))
charLength = 8
comp.append(0)

remainded = bitsMax
pad=bitsMax-charLength

string=""
i=0
while i < listLengh :
  compJoin = (comp[i]<<bitsMax)+comp[i+1]
  print("compJoin= "+str(bin(compJoin)))
  string += chr((compJoin>>(pad+remainded))%(2**charLength))
  print("addString= "+str(bin((compJoin>>(pad+remainded))%(2**charLength))))
  remainded = remainded - charLength
  if remainded <0:
    i=i+1
    remainded= remainded %bitsMax
print("string= "+string)




i=0
remainded=charLength
pad=bitsMax-charLength
compde=[]
while i < listLengh :
  compJoin = (comp[i]<<bitsMax)+comp[i+1]
  print("compJoin= "+str(bin(compJoin)))
  compde.append((compJoin>>(pad+remainded))%(2**bitsMax))
  print("addString= "+str(bin((compJoin>>(pad+remainded))%(2**bitsMax))))
  remainded = remainded - bitsMax
  if remainded <0:
    i=i+1
    remainded= remainded %bitsMax
print("compde= "+str(compde))