import purebin as pb

S1_MN_PATH = "src/parts/segment1_magic_number.bin"
S1_F3P_PATH = "src/parts/segment1_first3_pointers.bin"
S2_DATA_PATH = "src/parts/segment2_data.bin"
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
R1_12_DATA_CONTAINER = [R1_DATA_PATH, R2_DATA_PATH, R3_DATA_PATH, R4_DATA_PATH, R5_DATA_PATH, R6_DATA_PATH, R7_DATA_PATH, R8_DATA_PATH, R9_DATA_PATH, R10_DATA_PATH, R11_DATA_PATH, R12_DATA_PATH]

CUSTOM_DATA_2 = "src/samples/out.a18"
##########################################
#   CLASSES/FUNCTIONS
##########################################
class LTSDMFile:
    def __init__(self)->None:
        self.file = []
        self.head = []
        self.body = []
        self.data = [None, None, None, None, None, None, None, None, None, None, None, None] #List of bytes objects


    def add_frame(self, frame:int, binary:bytes)->None:
        if self.check_a18(binary):
            self.data[frame] = binary

    def check_a18(self, binary:bytes)->bool:
        # Get it as a string, then map it to check
        bitrate = int(binary[4:6], byteorder="little")
        if bitrate != 16000:
            return False
        return True
    
    def compile(self)->None:
        # Add LTSDM universal magic number
        with open(S1_MN_PATH, "rb") as bin:
            self.head += bin.read()
        #Placeholder for segment 1 secondary magic number, specific to each story data
        self.head += bytes(48)
        self.head += bytes(48)
        # Add the first 3 pointers, as they are constant beginnings
        with open(S1_F3P_PATH, "rb") as bin:
            self.head += bin.read()
    
        # This is where we would calculate the rest of the pointers (no empty frames allowed); also add pointers as you go
        for i in range(12):
            latest_pointer_int = len(self.body)
            hf = pb.HexFile()
            latest_pointer = pb.HexFile.decimalToHexString(hf, latest_pointer_int)
            self.head += bytes(latest_pointer)
            if self.data[i] is not None:
                self.body += self.data[i]
                
            else:
                self.body += R1_12_DATA_CONTAINER[i] #Placeholder for empty frames
        # Pad the rest of the file with "FF"
        padding_size = 1048576 - len(self.body)
        if padding_size > 0:
            self.body += b"FF" * padding_size
        with open("out.ltsdm", "wb") as bin:
            bin.write(self.file)

a = LTSDMFile()
a.add_frame(1,CUSTOM_DATA_2)
a.compile()