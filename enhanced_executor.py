"""
Enhanced ARM/Thumb Executor
Executes both ARM and Thumb instructions with mode switching
"""

from enhanced_decoder import EnhancedARMDecoder

class EnhancedARMExecutor:
    def __init__(self, cache=None):
        """Initialize the ARM/Thumb processor simulator"""
        # Cache simulator
        self.cache = cache
        # 16 general-purpose registers (R0-R15)
        self.registers = [0] * 16
        
        # Special register aliases
        # R13 = SP (Stack Pointer)
        # R14 = LR (Link Register)  
        # R15 = PC (Program Counter)
        self.SP = 13
        self.LR = 14
        self.PC = 15
        
        # Initialize stack pointer to a reasonable value
        self.registers[self.SP] = 0x1000
        
        # CPSR (Current Program Status Register)
        self.cpsr = 0
        
        # Memory (simple byte-addressable memory)
        self.memory = {}
        
        # Program memory
        self.program = []
        
        # Current instruction mode
        self.mode = "ARM"  # "ARM" or "Thumb"
        
        # Decoder
        self.decoder = EnhancedARMDecoder()
        
        # Execution control
        self.running = True
        self.instruction_count = 0
        self.max_instructions = 1000  # Prevent infinite loops
    
    def set_cpsr_flag(self, flag, value):
        """Set CPSR flags (N, Z, C, V)"""
        flag_positions = {'N': 31, 'Z': 30, 'C': 29, 'V': 28}
        if flag in flag_positions:
            pos = flag_positions[flag]
            if value:
                self.cpsr |= (1 << pos)
            else:
                self.cpsr &= ~(1 << pos)
    
    def get_cpsr_flag(self, flag):
        """Get CPSR flags"""
        flag_positions = {'N': 31, 'Z': 30, 'C': 29, 'V': 28}
        if flag in flag_positions:
            pos = flag_positions[flag]
            return bool(self.cpsr & (1 << pos))
        return False
    
    def update_flags(self, result):
        """Update CPSR flags based on result"""
        # Zero flag
        self.set_cpsr_flag('Z', result == 0)
        
        # Negative flag
        self.set_cpsr_flag('N', result < 0)
        
        # Note: Carry and Overflow flags would need more complex logic
        # For simplicity, we'll leave them as is for now
    
    def switch_mode(self, new_mode):
        """Switch between ARM and Thumb modes"""
        if new_mode in ["ARM", "Thumb"]:
            self.mode = new_mode
            self.decoder.set_mode(new_mode)
            print(f"Switched to {new_mode} mode")
        else:
            raise ValueError(f"Invalid mode: {new_mode}")
    
    def read_memory_word(self, address):
        """Read a 32-bit word from memory"""
        word = 0
        for i in range(4):
            byte_addr = address + i
            byte_val = self.memory.get(byte_addr, 0)
            word |= (byte_val << (i * 8))
        return word
    
    def write_memory_word(self, address, value):
        """Write a 32-bit word to memory"""
        for i in range(4):
            byte_addr = address + i
            byte_val = (value >> (i * 8)) & 0xFF
            self.memory[byte_addr] = byte_val
    
    def read_memory_halfword(self, address):
        """Read a 16-bit halfword from memory"""
        halfword = 0
        for i in range(2):
            byte_addr = address + i
            byte_val = self.memory.get(byte_addr, 0)
            halfword |= (byte_val << (i * 8))
        return halfword
    
    def write_memory_halfword(self, address, value):
        """Write a 16-bit halfword to memory"""
        for i in range(2):
            byte_addr = address + i
            byte_val = (value >> (i * 8)) & 0xFF
            self.memory[byte_addr] = byte_val
    
    def read_memory_byte(self, address):
        """Read a byte from memory"""
        return self.memory.get(address, 0)
    
    def write_memory_byte(self, address, value):
        """Write a byte to memory"""
        self.memory[address] = value & 0xFF
    
    def load_program_from_file(self, filename):
        """Load program from a text file containing hex instructions and optional mode switches"""
        self.program = []
        current_mode = "ARM"
        try:
            with open(filename, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith("//"):
                        continue

                    # Detect mode switches
                    if line.upper() == "# ARM MODE":
                        current_mode = "ARM"
                        continue
                    elif line.upper() in ("# THUMB MODE", "# THUMB"):
                        current_mode = "Thumb"
                        continue

                    # Strip inline comments
                    code_only = line.split('#')[0].strip()
                    if not code_only:
                        continue

                    try:
                        instr_val = int(code_only, 16)
                        self.program.append((instr_val, current_mode))
                    except ValueError:
                        print(f"Warning: Invalid instruction on line {line_num}: {line}")

            if not self.program:
                raise ValueError("No valid instructions found in file")

            # --- NEW: compute where Thumb region begins ---
            self.arm_count  = sum(1 for (_, m) in self.program if m == "ARM")
            self.thumb_base = self.arm_count * 4
            print(f"Loaded {len(self.program)} instructions "
                  f"(ARM={self.arm_count}, Thumb starts @0x{self.thumb_base:02X})")

        except FileNotFoundError:
            raise  # let main.py catch this


    
    def execute_program(self):
        """Run instructions until PC runs off the loaded program or max_instructions reached."""
        while self.running and self.instruction_count < self.max_instructions:
            pc_val = self.registers[self.PC]

            # --- NEW: pick the right index into self.program ---
            if self.mode == "ARM":
                instr_index = pc_val // 4
            else:
                # map PC to Thumb region in program list
                offset = pc_val - self.thumb_base
                instr_index = self.arm_count + (offset // 2)

            # out of bounds?
            if instr_index < 0 or instr_index >= len(self.program):
                print(f"PC beyond program bounds: PC=0x{pc_val:08X}")
                break

            instruction, instr_mode = self.program[instr_index]

            # mode switch if needed
            if self.mode != instr_mode:
                self.switch_mode(instr_mode)

            # execute & advance PC if unchanged by instruction
            if self.mode == "ARM":
                instruction &= 0xFFFFFFFF
                self.execute_arm_instruction(instruction)
                if self.registers[self.PC] == pc_val:
                    self.registers[self.PC] += 4
            else:
                instruction &= 0xFFFF
                self.execute_thumb_instruction(instruction)
                if self.registers[self.PC] == pc_val:
                    self.registers[self.PC] += 2

            self.instruction_count += 1

        if self.instruction_count >= self.max_instructions:
            print(f"Execution stopped: Maximum instruction limit ({self.max_instructions}) reached")

        # stats
        print(f"\nEXECUTION STATISTICS:")
        print("-" * 40)
        print(f"  Instructions executed: {self.instruction_count}")
        print(f"  Final PC: 0x{self.registers[self.PC]:08X}")

    
    def execute_arm_instruction(self, instruction):
        """Execute a single ARM instruction"""
        print(f"[{self.instruction_count:3d}] ARM PC=0x{self.registers[self.PC]:08X}: 0x{instruction:08X}", end=" ")
        
        # Decode the instruction
        instr_type, operands = self.decoder.decode_instruction(instruction, self.registers[self.PC], mode="ARM")
        print(f"-> {instr_type}")
        
        # Execute based on instruction type
        if instr_type == "MOV":
            self.execute_arm_mov(operands)
        elif instr_type == "MOV_IMM":
            self.execute_arm_mov_imm(operands)
        elif instr_type == "ADD":
            self.execute_arm_add(operands)
        elif instr_type == "ADD_IMM":
            self.execute_arm_add_imm(operands)
        elif instr_type == "SUB":
            self.execute_arm_sub(operands)
        elif instr_type == "SUB_IMM":
            self.execute_arm_sub_imm(operands)
        elif instr_type == "LDR":
            self.execute_arm_ldr(operands)
        elif instr_type == "STR":
            self.execute_arm_str(operands)
        elif instr_type == "CMP":
            self.execute_arm_cmp(operands)
        elif instr_type == "CMP_IMM":
            self.execute_arm_cmp_imm(operands)
        elif instr_type == "B":
            self.execute_arm_branch(operands)
        elif instr_type == "BL":
            self.execute_arm_branch_link(operands)
        elif instr_type == "MUL":
            self.execute_arm_mul(operands)
        elif instr_type == "AND":
            self.execute_arm_and(operands)
        elif instr_type == "ORR":
            self.execute_arm_orr(operands)
        elif instr_type == "BX":
            self.execute_arm_bx(operands)
        # ADD THE NEW INSTRUCTIONS HERE:
        elif instr_type == "EOR":
            self.execute_arm_eor(operands)
        elif instr_type == "EOR_IMM":
            self.execute_arm_eor_imm(operands)
        elif instr_type == "AND_IMM":
            self.execute_arm_and_imm(operands)
        elif instr_type == "ORR_IMM":
            self.execute_arm_orr_imm(operands)
        elif instr_type == "BIC":
            self.execute_arm_bic(operands)
        elif instr_type == "BIC_IMM":
            self.execute_arm_bic_imm(operands)
        elif instr_type == "MVN":
            self.execute_arm_mvn(operands)
        elif instr_type == "MVN_IMM":
            self.execute_arm_mvn_imm(operands)
        elif instr_type == "TST":
            self.execute_arm_tst(operands)
        elif instr_type == "TST_IMM":
            self.execute_arm_tst_imm(operands)
        elif instr_type == "TEQ":
            self.execute_arm_teq(operands)
        elif instr_type == "TEQ_IMM":
            self.execute_arm_teq_imm(operands)
        else:
            print(f"    Unimplemented ARM instruction: {instr_type}")
    
    def execute_thumb_instruction(self, instruction):
        """Execute a single Thumb instruction"""
        print(f"[{self.instruction_count:3d}] THM PC=0x{self.registers[self.PC]:08X}: 0x{instruction:04X}", end=" ")
        
        # Decode the instruction
        instr_type, operands = self.decoder.decode_thumb_instruction(instruction)
        print(f"-> {instr_type}")
        
        # Execute based on instruction type
        if instr_type == "T_MOV_IMM":
            self.execute_thumb_mov_imm(operands)
        elif instr_type == "T_ADD_IMM":
            self.execute_thumb_add_imm(operands)
        elif instr_type == "T_SUB_IMM":
            self.execute_thumb_sub_imm(operands)
        elif instr_type == "T_CMP_IMM":
            self.execute_thumb_cmp_imm(operands)
        elif instr_type == "T_ADD":
            self.execute_thumb_add(operands)
        elif instr_type == "T_SUB":
            self.execute_thumb_sub(operands)
        elif instr_type == "T_MOV_HI":
            self.execute_thumb_mov_hi(operands)
        elif instr_type == "T_LDR":
            self.execute_thumb_ldr(operands)
        elif instr_type == "T_STR":
            self.execute_thumb_str(operands)
        elif instr_type == "T_B":
            self.execute_thumb_branch(operands)
        elif instr_type == "T_BCC":
            self.execute_thumb_branch_conditional(operands)
        elif instr_type == "T_BX":
            self.execute_thumb_bx(operands)
        elif instr_type == "T_CMP":
            self.execute_thumb_cmp(operands)
        elif instr_type == "T_AND":
            self.execute_thumb_and(operands)
        elif instr_type == "T_EOR":
            self.execute_thumb_eor(operands)
        elif instr_type == "T_ORR":
            self.execute_thumb_orr(operands)
        elif instr_type == "T_MUL":
            self.execute_thumb_mul(operands)
        else:
            print(f"    Unimplemented Thumb instruction: {instr_type}")
    
    # ARM Instruction Implementations
    def execute_arm_mov(self, operands):
        """Execute ARM MOV instruction"""
        rd = operands['rd']
        rm = operands['rm']
        self.registers[rd] = self.registers[rm]
        print(f"    R{rd} = R{rm} = 0x{self.registers[rd]:08X}")
    
    def execute_arm_mov_imm(self, operands):
        """Execute ARM MOV immediate instruction"""
        rd = operands['rd']
        immediate = operands['immediate']
        self.registers[rd] = immediate
        print(f"    R{rd} = #{immediate} = 0x{immediate:08X}")
    
    def execute_arm_add(self, operands):
        """Execute ARM ADD instruction"""
        rd = operands['rd']
        rn = operands['rn']
        rm = operands['rm']
        result = self.registers[rn] + self.registers[rm]
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rn} + R{rm} = 0x{self.registers[rd]:08X}")
    
    def execute_arm_add_imm(self, operands):
        """Execute ARM ADD immediate instruction"""
        rd = operands['rd']
        rn = operands['rn']
        immediate = operands['immediate']
        result = self.registers[rn] + immediate
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rn} + #{immediate} = 0x{self.registers[rd]:08X}")
    
    def execute_arm_sub(self, operands):
        """Execute ARM SUB instruction"""
        rd = operands['rd']
        rn = operands['rn']
        rm = operands['rm']
        result = self.registers[rn] - self.registers[rm]
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rn} - R{rm} = 0x{self.registers[rd]:08X}")
    
    def execute_arm_sub_imm(self, operands):
        """Execute ARM SUB immediate instruction"""
        rd = operands['rd']
        rn = operands['rn']
        immediate = operands['immediate']
        result = self.registers[rn] - immediate
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rn} - #{immediate} = 0x{self.registers[rd]:08X}")
    
    def execute_arm_mul(self, operands):
        """Execute ARM MUL instruction"""
        rd = operands['rd']
        rm = operands['rm']
        rs = operands['rs']
        result = self.registers[rm] * self.registers[rs]
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rm} * R{rs} = 0x{self.registers[rd]:08X}")
    
    def execute_arm_and(self, operands):
        """Execute ARM AND instruction"""
        rd = operands['rd']
        rn = operands['rn']
        rm = operands['rm']
        result = self.registers[rn] & self.registers[rm]
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rn} & R{rm} = 0x{self.registers[rd]:08X}")
    
    def execute_arm_orr(self, operands):
        """Execute ARM ORR instruction"""
        rd = operands['rd']
        rn = operands['rn']
        rm = operands['rm']
        result = self.registers[rn] | self.registers[rm]
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rn} | R{rm} = 0x{self.registers[rd]:08X}")
    
    def execute_arm_cmp(self, operands):
        """Execute ARM CMP instruction"""
        rn = operands['rn']
        rm = operands['rm']
        result = self.registers[rn] - self.registers[rm]
        self.update_flags(result)
        print(f"    CMP R{rn}, R{rm} (result: {result})")
    
    def execute_arm_cmp_imm(self, operands):
        """Execute ARM CMP immediate instruction"""
        rn = operands['rn']
        immediate = operands['immediate']
        result = self.registers[rn] - immediate
        self.update_flags(result)
        print(f"    CMP R{rn}, #{immediate} (result: {result})")
    
    def execute_arm_str(self, operands):
        """Execute ARM STR instruction with cache simulation"""
        rd = operands['rd']
        rn = operands['rn']
        offset = operands['offset']
        address = self.registers[rn] + offset
        value = self.registers[rd]
    
        # Simulate cache access for instruction fetch
        if self.cache:
            self.cache.access_instruction(self.registers[self.PC])
            self.cache.access_data(address, is_write=True)
    
        self.write_memory_word(address, value)
        print(f"    MEM[R{rn}+{offset}] = MEM[0x{address:08X}] = R{rd} = 0x{value:08X}")

    
    def execute_arm_branch(self, operands):
        """Execute ARM B instruction"""
        offset = operands['offset']
        # Sign extend 24-bit offset and shift left by 2
        if offset & 0x800000:
            offset |= 0xFF000000
        branch_offset = offset << 2
        old_pc = self.registers[self.PC]
        self.registers[self.PC] = (old_pc + 8 + branch_offset) & 0xFFFFFFFF
        print(f"    Branch from 0x{old_pc:08X} to 0x{self.registers[self.PC]:08X}")
    
    def execute_arm_branch_link(self, operands):
        """Execute ARM BL instruction"""
        offset = operands['offset']
        # Save return address
        self.registers[self.LR] = self.registers[self.PC] + 4
        # Sign extend 24-bit offset and shift left by 2
        if offset & 0x800000:
            offset |= 0xFF000000
        branch_offset = offset << 2
        old_pc = self.registers[self.PC]
        self.registers[self.PC] = (old_pc + 8 + branch_offset) & 0xFFFFFFFF
        print(f"    BL from 0x{old_pc:08X} to 0x{self.registers[self.PC]:08X}, LR=0x{self.registers[self.LR]:08X}")
    
    def execute_arm_bx(self, operands):
        """Execute ARM BX instruction"""
        rm = operands['rm']
        target = self.registers[rm]
        if target & 1:
            # Switch to Thumb mode
            self.switch_mode("Thumb")
            self.registers[self.PC] = target & 0xFFFFFFFE
        else:
            # Stay in ARM mode
            self.switch_mode("ARM")
            self.registers[self.PC] = target & 0xFFFFFFFC
        print(f"    BX R{rm} to 0x{self.registers[self.PC]:08X} ({self.mode} mode)")
        
    def execute_arm_eor(self, operands):
        """Execute ARM EOR (XOR) instruction"""
        rd = operands['rd']
        rn = operands['rn']
        rm = operands['rm']
        result = self.registers[rn] ^ self.registers[rm]
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rn} ^ R{rm} = 0x{self.registers[rd]:08X}")

    def execute_arm_eor_imm(self, operands):
        """Execute ARM EOR immediate instruction"""
        rd = operands['rd']
        rn = operands['rn']
        immediate = operands['immediate']
        result = self.registers[rn] ^ immediate
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rn} ^ #{immediate} = 0x{self.registers[rd]:08X}")

    def execute_arm_bic(self, operands):
        """Execute ARM BIC (Bit Clear) instruction"""
        rd = operands['rd']
        rn = operands['rn']
        rm = operands['rm']
        result = self.registers[rn] & ~self.registers[rm]
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rn} & ~R{rm} = 0x{self.registers[rd]:08X}")

    def execute_arm_mvn(self, operands):
        """Execute ARM MVN (Move NOT) instruction"""
        rd = operands['rd']
        rm = operands['rm']
        result = ~self.registers[rm]
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = ~R{rm} = 0x{self.registers[rd]:08X}")

    def execute_arm_tst(self, operands):
        """Execute ARM TST (Test) instruction"""
        rn = operands['rn']
        rm = operands['rm']
        result = self.registers[rn] & self.registers[rm]
        self.update_flags(result)
        print(f"    TST R{rn}, R{rm} (result: 0x{result:08X})")

    def execute_arm_teq(self, operands):
        """Execute ARM TEQ (Test Exclusive) instruction"""
        rn = operands['rn']
        rm = operands['rm']
        result = self.registers[rn] ^ self.registers[rm]
        self.update_flags(result)
        print(f"    TEQ R{rn}, R{rm} (result: 0x{result:08X})")
        
    def execute_arm_and_imm(self, operands):
        """Execute ARM AND immediate instruction"""
        rd = operands['rd']
        rn = operands['rn']
        immediate = operands['immediate']
        result = self.registers[rn] & immediate
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rn} & #{immediate} = 0x{self.registers[rd]:08X}")

    def execute_arm_orr_imm(self, operands):
        """Execute ARM ORR immediate instruction"""
        rd = operands['rd']
        rn = operands['rn']
        immediate = operands['immediate']
        result = self.registers[rn] | immediate
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rn} | #{immediate} = 0x{self.registers[rd]:08X}")

    def execute_arm_bic_imm(self, operands):
        """Execute ARM BIC immediate instruction"""
        rd = operands['rd']
        rn = operands['rn']
        immediate = operands['immediate']
        result = self.registers[rn] & ~immediate
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rn} & ~#{immediate} = 0x{self.registers[rd]:08X}")

    def execute_arm_mvn_imm(self, operands):
        """Execute ARM MVN immediate instruction"""
        rd = operands['rd']
        immediate = operands['immediate']
        result = ~immediate
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = ~#{immediate} = 0x{self.registers[rd]:08X}")

    def execute_arm_tst_imm(self, operands):
        """Execute ARM TST immediate instruction"""
        rn = operands['rn']
        immediate = operands['immediate']
        result = self.registers[rn] & immediate
        self.update_flags(result)
        print(f"    TST R{rn}, #{immediate} (result: 0x{result:08X})")

    def execute_arm_teq_imm(self, operands):
        """Execute ARM TEQ immediate instruction"""
        rn = operands['rn']
        immediate = operands['immediate']
        result = self.registers[rn] ^ immediate
        self.update_flags(result)
        print(f"    TEQ R{rn}, #{immediate} (result: 0x{result:08X})")
    
    # Thumb Instruction Implementations
    def execute_thumb_mov_imm(self, operands):
        """Execute Thumb MOV immediate instruction"""
        rd = operands['rd']
        immediate = operands['immediate']
        self.registers[rd] = immediate
        print(f"    R{rd} = #{immediate} = 0x{immediate:08X}")
    
    def execute_thumb_add_imm(self, operands):
        """Execute Thumb ADD immediate instruction"""
        rd = operands['rd']
        immediate = operands['immediate']
        result = self.registers[rd] + immediate
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rd} + #{immediate} = 0x{self.registers[rd]:08X}")
        
    def execute_thumb_cmp(self, operands):
        """Execute Thumb CMP register instruction"""
        rd = operands['rd']
        rs = operands['rs']
        result = self.registers[rd] - self.registers[rs]
        self.update_flags(result)
        print(f"    CMP R{rd}, R{rs} (result: {result})")
    
    def execute_thumb_sub_imm(self, operands):
        """Execute Thumb SUB immediate instruction"""
        rd = operands['rd']
        immediate = operands['immediate']
        result = self.registers[rd] - immediate
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rd} - #{immediate} = 0x{self.registers[rd]:08X}")
    
    def execute_thumb_cmp_imm(self, operands):
        """Execute Thumb CMP immediate instruction"""
        rd = operands['rd']
        immediate = operands['immediate']
        result = self.registers[rd] - immediate
        self.update_flags(result)
        print(f"    CMP R{rd}, #{immediate} (result: {result})")
    
    def execute_thumb_add(self, operands):
        """Execute Thumb ADD instruction"""
        rd = operands['rd']
        rs = operands['rs']
        result = self.registers[rd] + self.registers[rs]
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rd} + R{rs} = 0x{self.registers[rd]:08X}")
    
    def execute_thumb_sub(self, operands):
        """Execute Thumb SUB instruction"""
        rd = operands['rd']
        rs = operands['rs']
        result = self.registers[rd] - self.registers[rs]
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rd} - R{rs} = 0x{self.registers[rd]:08X}")
    
    def execute_thumb_mov_hi(self, operands):
        """Execute Thumb MOV high register instruction"""
        rd = operands['rd']
        rs = operands['rs']
        self.registers[rd] = self.registers[rs]
        print(f"    R{rd} = R{rs} = 0x{self.registers[rd]:08X}")
    
    def execute_thumb_ldr(self, operands):
        """Execute Thumb LDR instruction"""
        rd = operands['rd']
        rb = operands['rb']
        offset = operands['offset']
        address = self.registers[rb] + (offset << 2)
        value = self.cache.access_data(address) if self.cache else self.read_memory_word(address)
        self.registers[rd] = value
        print(f"    R{rd} = MEM[R{rb}+{offset<<2}] = MEM[0x{address:08X}] = 0x{value:08X}")
    
    def execute_thumb_str(self, operands):
        """Execute Thumb STR instruction"""
        rd = operands['rd']
        rb = operands['rb']
        offset = operands['offset']
        address = self.registers[rb] + (offset << 2)
        value = self.registers[rd]
        self.cache.access_data(address, is_write=True) if self.cache else None
        print(f"    MEM[R{rb}+{offset<<2}] = MEM[0x{address:08X}] = R{rd} = 0x{value:08X}")
    
    def execute_thumb_branch(self, operands):
        """Execute Thumb unconditional branch"""
        offset = operands['offset']
        # Sign extend and shift left by 1
        branch_offset = offset << 1
        old_pc = self.registers[self.PC]
        self.registers[self.PC] = (old_pc + 4 + branch_offset) & 0xFFFFFFFF
        print(f"    Branch from 0x{old_pc:08X} to 0x{self.registers[self.PC]:08X}")
    
    def execute_thumb_branch_conditional(self, operands):
        """Execute Thumb conditional branch"""
        condition = operands['condition']
        offset = operands['offset']
        
        # Check condition
        should_branch = self.check_condition(condition)
        
        if should_branch:
            branch_offset = offset << 1
            old_pc = self.registers[self.PC]
            self.registers[self.PC] = (old_pc + 4 + branch_offset) & 0xFFFFFFFF
            print(f"    Conditional branch taken from 0x{old_pc:08X} to 0x{self.registers[self.PC]:08X}")
        else:
            print(f"    Conditional branch not taken")
    
    def execute_thumb_bx(self, operands):
        """Execute Thumb BX instruction"""
        rs = operands['rs']
        target = self.registers[rs]
        if target & 1:
            # Stay in Thumb mode
            self.switch_mode("Thumb")
            self.registers[self.PC] = target & 0xFFFFFFFE
        else:
            # Switch to ARM mode
            self.switch_mode("ARM")
            self.registers[self.PC] = target & 0xFFFFFFFC
        print(f"    BX R{rs} to 0x{self.registers[self.PC]:08X} ({self.mode} mode)")
        
    def execute_thumb_and(self, operands):
        """Execute Thumb AND instruction"""
        rd = operands['rd']
        rs = operands['rs']
        result = self.registers[rd] & self.registers[rs]
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rd} & R{rs} = 0x{self.registers[rd]:08X}")

    def execute_thumb_eor(self, operands):
        """Execute Thumb EOR instruction"""
        rd = operands['rd']
        rs = operands['rs']
        result = self.registers[rd] ^ self.registers[rs]
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rd} ^ R{rs} = 0x{self.registers[rd]:08X}")

    def execute_thumb_orr(self, operands):
        """Execute Thumb ORR instruction"""
        rd = operands['rd']
        rs = operands['rs']
        result = self.registers[rd] | self.registers[rs]
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rd} | R{rs} = 0x{self.registers[rd]:08X}")

    def execute_thumb_mul(self, operands):
        """Execute Thumb MUL instruction"""
        rd = operands['rd']
        rs = operands['rs']
        result = self.registers[rd] * self.registers[rs]
        self.registers[rd] = result & 0xFFFFFFFF
        print(f"    R{rd} = R{rd} * R{rs} = 0x{self.registers[rd]:08X}")
    
    def check_condition(self, condition):
        """Check ARM condition codes"""
        conditions = {
            0x0: lambda: self.get_cpsr_flag('Z'),           # EQ
            0x1: lambda: not self.get_cpsr_flag('Z'),       # NE
            0x2: lambda: self.get_cpsr_flag('C'),           # CS/HS
            0x3: lambda: not self.get_cpsr_flag('C'),       # CC/LO
            0x4: lambda: self.get_cpsr_flag('N'),           # MI
            0x5: lambda: not self.get_cpsr_flag('N'),       # PL
            0x6: lambda: self.get_cpsr_flag('V'),           # VS
            0x7: lambda: not self.get_cpsr_flag('V'),       # VC
            0x8: lambda: self.get_cpsr_flag('C') and not self.get_cpsr_flag('Z'),  # HI
            0x9: lambda: not self.get_cpsr_flag('C') or self.get_cpsr_flag('Z'),   # LS
            0xA: lambda: self.get_cpsr_flag('N') == self.get_cpsr_flag('V'),       # GE
            0xB: lambda: self.get_cpsr_flag('N') != self.get_cpsr_flag('V'),       # LT
            0xC: lambda: not self.get_cpsr_flag('Z') and (self.get_cpsr_flag('N') == self.get_cpsr_flag('V')),  # GT
            0xD: lambda: self.get_cpsr_flag('Z') or (self.get_cpsr_flag('N') != self.get_cpsr_flag('V')),       # LE
            0xE: lambda: True,                              # AL (always)
            0xF: lambda: False                              # NV (never)
        }
        return conditions.get(condition, lambda: False)()
    
    def execute_arm_ldr(self, operands):
        """Execute ARM LDR instruction with cache simulation"""
        rd = operands['rd']
        rn = operands['rn']
        offset = operands['offset']
        address = self.registers[rn] + offset
    
        # Simulate cache access for instruction fetch
        if self.cache:
            self.cache.access_instruction(self.registers[self.PC])
            self.cache.access_data(address, is_write=False)
    
        value = self.read_memory_word(address)
        self.registers[rd] = value
        print(f"    R{rd} = MEM[R{rn}+{offset}] = MEM[0x{address:08X}] = 0x{value:08X}")

    
    def display_state(self):
        """Display final processor state"""
        print("REGISTER STATE:")
        print("-" * 40)
        for i in range(16):
            name = f"R{i}"
            if i == 13: name = "SP (R13)"
            elif i == 14: name = "LR (R14)"
            elif i == 15: name = "PC (R15)"
            print(f"  {name:>8}: 0x{self.registers[i]:08X} ({self.registers[i]:>10d})")
        
        print(f"\nPROCESSOR STATUS:")
        print("-" * 40)
        print(f"  Mode: {self.mode}")
        print(f"  CPSR: 0x{self.cpsr:08X}")
        flags = []
        for flag in ['N', 'Z', 'C', 'V']:
            flags.append(flag if self.get_cpsr_flag(flag) else '-')
        print(f"  Flags: {''.join(flags)}")
        
        print(f"\nEXECUTION STATISTICS:")
        print("-" * 40)
        print(f"  Instructions executed: {self.instruction_count}")
        print(f"  Final PC: 0x{self.registers[self.PC]:08X}")
        
        # Show non-zero memory locations
        non_zero_mem = {addr: val for addr, val in self.memory.items() if val != 0}
        if non_zero_mem:
            print(f"\nMEMORY STATE (non-zero locations):")
            print("-" * 40)
            for addr in sorted(non_zero_mem.keys())[:10]:  # Show first 10
                print(f"  0x{addr:08X}: 0x{non_zero_mem[addr]:02X}")
            if len(non_zero_mem) > 10:
                print(f"  ... and {len(non_zero_mem) - 10} more locations")