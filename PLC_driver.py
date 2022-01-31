import snap7
import math
class PLC(snap7.client.Client):
    def __init__(self, ip, rack, slot):
        self.ip = ip
        self.rack = rack
        self.slot = slot
        self = super().__init__()
    
    def connect(self):
        super().connect(self.ip, self.rack, self.slot)
    
    def add_dataBlock(self, db_number):
        return self.DataBlock(self, db_number) 

    class DataBlock(object):
        def __init__(self, object, db_num):
            self.plc = object
            self.db_num = db_num

        def add_boolArray(self, start, num_elements):
            return self.BoolArray(self, start, num_elements)

        def add_boolVariable(self, start, index):
            return self.BoolVariable(self, start, index)

        def add_timevarible(self, start):
            return self.Variable(self, start)

        def add_timeArray(self, start, num_Elements):
            array = self.TimeArray(self, start, num_Elements)
            return array

        class BoolArray(object):
            def __init__(self, object, start, num_elements) -> None:
                self.plc =  object.plc
                self.start = start
                self.num_elements = num_elements
                self.db_num = object.db_num
                array = []
                for i in range(num_elements):
                    memory_address = start + (i//8)
                    j =  i % 8
                    element = object.BoolVariable(object, memory_address, j)
                    array.append(element)
                self.array = array 

            def __getitem__(self, item):
                return self.array[item]

            def clear(self):
                size = self.num_elements // 8
                value = 0
                byte_array = value.to_bytes(size, 'big') 
                self.plc.db_write(self.db_num, self.start, byte_array)

            def complete_bytes(self, bit_array):
                i = len(bit_array)
                size  = math.ceil(i / 8)
                while i < (size * 8):
                    bit_array.append(0)
                    i +=1
                return bit_array

            def display(self):
                size = self.num_elements // 8
                for i in range(size):
                    memory_address = self.start + i 
                    hexValue = self.plc.db_read(self.db_num, memory_address, 1)
                    value = int.from_bytes(hexValue, 'big')
                    print("Byte {0}: {1}".format(i, value))

            def make_bitString(self, bit_array):
                string = ''
                i = 0
                for bit in bit_array:
                    if i % 8 == 0:
                        string = string + ' '
                    string = string + str(bit)
                    i += 1   
                return string  

            def make_byteArray(self, bit_array):
                bit_array = self.complete_bytes(bit_array)
                bit_array.reverse()
                string = self.make_bitString(bit_array)
                values = string.split()
                values.reverse()
                values = [int(value, 2) for value in values]
                byte_array = bytearray(values) 
                return byte_array, len(values)
            
            def write(self, bit_array):
                [byte_array, num_bytes] = self.make_byteArray(bit_array) 
                self.plc.db_write(self.db_num, self.start, byte_array)

        class BoolVariable(object):
            def __init__(self, object, start, index) -> None:
                self.start = start
                self.plc = object.plc
                self.db_num = object.db_num
                self.index = index

            def display(self):
                bit = self.get_bit()
                print(bit)

            def display_buffer(self):
                byte = self.get_buffer()
                buffer = int.from_bytes(byte, 'big')
                print(buffer)

            def get_bit(self):
                byte = self.get_buffer()
                mask =  2 ** self.index
                byte = int.from_bytes(byte, 'big')
                mask = byte & mask
                bit = mask >> self.index
                return bit

            def get_buffer(self):
                return self.plc.db_read(self.db_num, self.start, 1)

            def off(self):
                byte = self.get_buffer()
                byte = int.from_bytes(byte, 'big')
                mask =  2 ** self.index
                mask = 255 - mask
                mask = byte & mask
                byte = mask.to_bytes(1, 'big') 
                self.plc.db_write(self.db_num, self.start, byte)
            
            def on(self):
                byte = self.get_buffer()
                byte = int.from_bytes(byte, 'big')
                mask = 2 ** self.index
                mask = byte | mask
                byte = mask.to_bytes(1, 'big') 
                self.plc.db_write(self.db_num, self.start, byte) 

        class TimeArray(object):
            def __init__(self, object, start, num_elements) -> None:
                self.start = start
                self.num_elements =  num_elements
                self.plc =  object.plc
                self.db_num = object.db_num
                self.object = object

            def __getitem__(self, item):
                return self.object.TimeVariable(self.object, self.start + (item * 4)) 

            def clear(self):
                zeros = [0] * self.num_elements
                self.write(zeros)
            
            def write(self, value_array):
                byte_array = bytearray()
                for value in value_array:
                    byte_array += value.to_bytes(4, 'big')
                self.plc.db_write(self.db_num, self.start, byte_array)

        class TimeVariable(object):
            def __init__(self, object, start, size = 4):
                self.start = start
                self.size = size
                self.plc = object.plc
                self.db_num = object.db_num

            def clear(self):
                self.write(0)

            def display(self):
                hexValue = self.plc.db_read(self.db_num, self.start, self.size)
                value = int.from_bytes(hexValue, byteorder='big')
                print("Value: {0}".format(value))
            
            def display_hex(self):
                hexValue = self.plc.db_read(self.db_num, self.start, self.size)
                print("Hexadecimal value: {0}".format(hexValue))
            
            def write(self, value_ms):
                byte_array = value_ms.to_bytes(4, 'big') 
                self.plc.db_write(self.db_num, self.start, byte_array)
        

IP = '192.168.0.102'
RACK = 0
SLOT = 1

MY_DATABLOCK = 3 # DB Number
START_ADDRESS = 1040 #Variable address

plc = PLC(IP, RACK, SLOT)
plc.connect()

# Example
block = plc.add_dataBlock(MY_DATABLOCK)
timers = block.add_timeArray(START_ADDRESS, 8)
timers.write([1000, 2000, 3000]) # 
