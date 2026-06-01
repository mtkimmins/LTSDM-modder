S1_MN_PATH = "src/parts/magic-number-LTSDM.bin"
S1_F3P_PATH = "src/parts/segment1-first-three-pointers.bin"
S2_DATA_PATH = "src/parts/segment2.bin"
R1_DATA_PATH = "src/parts/region1.bin"
R2_DATA_PATH = "src/parts/region2.bin"
R3_DATA_PATH = "src/parts/region3.bin"
R4_DATA_PATH = "src/parts/region4.bin"
R5_DATA_PATH = "src/parts/region5.bin"
R6_DATA_PATH = "src/parts/region6.bin"
R7_DATA_PATH = "src/parts/region7.bin"
R8_DATA_PATH = "src/parts/region8.bin"
R9_DATA_PATH = "src/parts/region9.bin"
R10_DATA_PATH = "src/parts/region10.bin"
R11_DATA_PATH = "src/parts/region11.bin"
R12_DATA_PATH = "src/parts/region12.bin"
R13_DATA_PATH = "src/parts/region13.bin"
R14_DATA_PATH = "src/parts/region14.bin"
R15_DATA_PATH = "src/parts/region15.bin"
R16_DATA_PATH = "src/parts/region16.bin"
R17_DATA_PATH = "src/parts/region17.bin"
R18_DATA_PATH = "src/parts/region18.bin"
R19_DATA_PATH = "src/parts/region19.bin"
R20_DATA_PATH = "src/parts/region20.bin"
R21_DATA_PATH = "src/parts/region21.bin"
R22_DATA_PATH = "src/parts/region22.bin"
R23_DATA_PATH = "src/parts/region23.bin"
R24_DATA_PATH = "src/parts/region24.bin"

class CartridgeData:
    def __init__(self):
        self.length:int =  1048576 # constant, files should be 1Mib exactly
        
        self.magic_number:list = []
        self.pointers:list = [[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[]] #list of lists of 4 bytes, each representing a pointer
        self.segment2:list = []
        self.regions:list = [[],[],[],[],[],[],[],[],[],[],[],[]] # list of first 12 regions
        self.segment5:list = [] # list of conserved regions (segment 5)

        # Load and create the magic number
        with open(S1_MN_PATH, "rb") as bin:
            self.magic_number = list(hex(x) for x in bin.read())
            self.magic_number.append(hex(255))
            self.magic_number.append(hex(255))

        # Load and create the first 3 pointers
        with open(S1_F3P_PATH, "rb") as bin:
            for i in range(3):
                self.pointers[i] = list(hex(x) for x in bin.read(4)) # 4 bytes at a time, for each pointer
            # print(self.pointers)

        # Load segment 2 data
        with open(S2_DATA_PATH, "rb") as bin:
            self.segment2 = list(hex(x) for x in bin.read())

        # Load segment 5 data (conserved regions)
        with open(R13_DATA_PATH, "rb") as bin:
            self.segment5 += list(hex(x) for x in bin.read())
        with open(R14_DATA_PATH, "rb") as bin:
            self.segment5 += list(hex(x) for x in bin.read())
        with open(R15_DATA_PATH, "rb") as bin:
            self.segment5 += list(hex(x) for x in bin.read())
        with open(R16_DATA_PATH, "rb") as bin:
            self.segment5 += list(hex(x) for x in bin.read())
        with open(R17_DATA_PATH, "rb") as bin:  
            self.segment5 += list(hex(x) for x in bin.read())
        with open(R18_DATA_PATH, "rb") as bin:
            self.segment5 += list(hex(x) for x in bin.read())
        with open(R19_DATA_PATH, "rb") as bin:
            self.segment5 += list(hex(x) for x in bin.read())
        with open(R20_DATA_PATH, "rb") as bin:
            self.segment5 += list(hex(x) for x in bin.read())
        with open(R21_DATA_PATH, "rb") as bin:
            self.segment5 += list(hex(x) for x in bin.read())
        with open(R22_DATA_PATH, "rb") as bin:
            self.segment5 += list(hex(x) for x in bin.read())
        with open(R23_DATA_PATH, "rb") as bin:
            self.segment5 += list(hex(x) for x in bin.read())
        with open(R24_DATA_PATH, "rb") as bin:
            self.segment5 += list(hex(x) for x in bin.read())

        self.calculatePointers()

        self.available_room = self.length - len(self.magic_number) - (len(self.pointers) * 4) - len(self.segment2) - len(self.segment5) - 128 # the last section incorporating Segments 6 and 7, to buffer against the edge
        print("Available room for regions 1-12: " + str(self.available_room))

    def addRegion(self, region_data:list, index:int)->bool:
        if len(region_data) > self.available_room:
            print("Region data is too large to fit in the cartridge data.")
            return False
        self.regions.insert(index, region_data)
        self.available_room -= len(region_data)
        return True
    
    def calculatePointers(self)->None:
        # Calculate the end of Segment 2
        segment2_end = len(self.magic_number) + (len(self.pointers) * 4) + len(self.segment2)
        # Calculate the pointers for regions 1-12
        for i in range(len(self.regions)):
            region_start = segment2_end + sum(len(region) for region in self.regions[:i])
            self.pointers[i] = hex(region_start)
            print(self.pointers)
            # pointer_bytes = pointer_value.to_bytes(4, byteorder="little")
            # self.pointers[i] = list(pointer_bytes)
    
    def compile(self)->bytes:
        with open("src/samples/custom.bin", "wb") as bin:
            # Write the magic number
            bin.write(self.magic_number)
            # Write the pointers
            for pointer in self.pointers:
                bin.write(pointer)
            # Write segment 2
            bin.write(self.segment2)
            # Write regions 1-12
            for region in self.regions:
                bin.write(region)
            # Write segment 5 (conserved regions)
            bin.write(self.segment5)
            # Fill the rest with 255
            remaining_bytes = self.length - len(self.magic_number) - (len(self.pointers) * 4) - len(self.segment2) - len(self.segment5) - sum(len(region) for region in self.regions)
            bin.write([255] * remaining_bytes)

c = CartridgeData()
print(c.magic_number)
