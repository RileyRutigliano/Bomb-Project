target = 5
print(target)
b_target = bin(target)[2:].zfill(5) #5 for wires and 4 for toggles
print (b_target)
l_target =[]
for bit in b_target:
    l_target.append(bool(int(bit)))
    print (l_target) 

bitstring = []
for bit in l_target:
    bitstring.append(str(int(bit)))
print(bitstring)
bitstring = "".join(bitstring)
print(bitstring)
value = int(bitstring, 2)
print(value)

#bin(target)[2:].zfill(5) #5 for wires and 4 for toggles

def _get_int_state(self):
    state = []
    for pin in self._component:
        state.append(pin.value)
    # state = [F, T, T, F]
    value = []
    for s in state:
        value.append(str(int(s)))
        
        