# ================================================================
# FILE: ARM_Executor.py
# DESCRIPTION: Executes 32-bit ARM instructions for CP216 simulator
# ================================================================

class ARMExecutor:
    def __init__(self):
        self.registers = [0] * 16  # R0-R15, with R15 = PC
        self.memory = [0] * 1024   # Basic memory simulation
        self.instructions = []     # Loaded machine code
        self.pc = 0                # Program Counter (R15)
        self.flags = {'N': 0, 'Z': 0, 'C': 0, 'V': 0}  # Status flags
        self.debug_mode = True     # Show debug output

    def load_program_from_file(self, filename):
        with open(filename, 'r') as file:
            self.instructions = []
            for line in file:
                line = line.strip()
                if line and not line.startswith('#'):
                    self.instructions.append(int(line, 16))

    def decode_instruction(self, instruction, address):
        opcode = (instruction >> 21) & 0xF
        rn = (instruction >> 16) & 0xF
        rd = (instruction >> 12) & 0xF
        operand2 = instruction & 0xFFF

        if (instruction & 0x0FE00000) == 0x00800000:
            return f"ADD R{rd}, R{rn}, #{operand2}"
        elif (instruction & 0x0FE00000) == 0x00400000:
            return f"SUB R{rd}, R{rn}, #{operand2}"
        elif (instruction & 0x0FE00000) == 0x03A00000:
            return f"MOV R{rd}, #{operand2}"
        elif (instruction & 0x0FE00000) == 0x01A00000:
            return f"MOV R{rd}, R{operand2 & 0xF}"
        elif (instruction & 0x0FE00000) == 0x00200000:
            return f"EOR R{rd}, R{rn}, #{operand2}"
        elif (instruction & 0x0FE00000) == 0x00000000:
            return f"AND R{rd}, R{rn}, #{operand2}"
        elif (instruction & 0x0FE00000) == 0x03800000:
            return f"ORR R{rd}, R{rn}, #{operand2}"
        elif (instruction & 0x0F000000) == 0x0A000000:
            offset = instruction & 0x00FFFFFF
            return f"B {offset}"
        elif (instruction & 0x0F000000) == 0x0B000000:
            offset = instruction & 0x00FFFFFF
            return f"BL {offset}"
        elif (instruction & 0x0FBF0FFF) == 0x01A0F00E:
            return "MOV PC, LR"
        elif (instruction & 0x0FBF0FFF) == 0x012FFF1E:
            return "BX LR"
        elif (instruction & 0xFF000000) == 0xEF000000:
            imm = instruction & 0x00FFFFFF
            return f"SWI #{imm}"
        else:
            return "UNKNOWN"


    def execute_program(self):
        self.pc = 0
        while self.pc // 4 < len(self.instructions):
            instr = self.instructions[self.pc // 4]
            if self.debug_mode:
                print(f"0x{self.pc:04X}: 0x{instr:08X} -> {self.decode_instruction(instr, self.pc)}")
            self.execute_instruction(instr)
            self.pc += 4

    def execute_instruction(self, instruction):
        opcode = (instruction >> 21) & 0xF
        rn = (instruction >> 16) & 0xF
        rd = (instruction >> 12) & 0xF
        operand2 = instruction & 0xFFF

        if (instruction & 0x0FE00000) == 0x00800000:  # ADD
            self.registers[rd] = self.registers[rn] + operand2
        elif (instruction & 0x0FE00000) == 0x00400000:  # SUB
            self.registers[rd] = self.registers[rn] - operand2
        elif (instruction & 0x0FE00000) == 0x03A00000:  # MOV immediate
            self.registers[rd] = operand2
        elif (instruction & 0x0FE00000) == 0x01A00000:  # MOV register
            self.registers[rd] = self.registers[operand2 & 0xF]
        elif (instruction & 0x0FE00000) == 0x00200000:  # EOR
            self.registers[rd] = self.registers[rn] ^ operand2
        elif (instruction & 0x0FE00000) == 0x00000000:  # AND
            self.registers[rd] = self.registers[rn] & operand2
        elif (instruction & 0x0FE00000) == 0x03800000:  # ORR
            self.registers[rd] = self.registers[rn] | operand2
        elif (instruction & 0x0F000000) == 0x0A000000:  # B
            offset = instruction & 0x00FFFFFF
            if offset & 0x00800000:
                offset |= 0xFF000000  # Sign extend negative
            self.pc += (offset << 2)
            self.pc -= 4
        elif (instruction & 0x0FBF0FFF) == 0x01A0F00E:  # MOV PC, LR
            self.pc = self.registers[14]
        elif (instruction & 0x0FBF0FFF) == 0x012FFF1E:  # BX LR
            self.pc = self.registers[14]
        elif (instruction & 0xFF000000) == 0xEF000000:  # SWI
            imm = instruction & 0x00FFFFFF
            print(f"SWI #{imm} (Software Interrupt)")
            if imm == 0x11:
                print("SWI HALT invoked. Ending execution.")
                self.pc = len(self.instructions) * 4

    def display_state(self):
        for i in range(16):
            print(f"R{i}: 0x{self.registers[i]:08X}", end='  ')
            if i % 4 == 3:
                print()
        print(f"Flags: N={self.flags['N']} Z={self.flags['Z']} C={self.flags['C']} V={self.flags['V']}")
