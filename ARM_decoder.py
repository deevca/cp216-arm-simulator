# ================================================================
# FILE: ARM_decoder.py
# DESCRIPTION: Decodes 32-bit ARM instructions into human-readable format
# ================================================================

class ARMDecoder:
    def __init__(self):
        self.registers = {
            0: 'R0', 1: 'R1', 2: 'R2', 3: 'R3',
            4: 'R4', 5: 'R5', 6: 'R6', 7: 'R7',
            8: 'R8', 9: 'R9', 10: 'R10', 11: 'R11',
            12: 'R12', 13: 'SP', 14: 'LR', 15: 'PC'
        }

    def decode_instruction(self, instruction, address=0):
        """
        Decode a 32-bit ARM instruction into (mnemonic, operand_dict)
        """
        cond = (instruction >> 28) & 0xF
        opcode = (instruction >> 21) & 0xF
        i_flag = (instruction >> 25) & 0x1
        instr_type = (instruction >> 26) & 0x3

        # Check for special instructions first
        # MUL instruction
        if instr_type == 0b00 and (instruction & 0x0FC000F0) == 0x00000090:
            rd = (instruction >> 16) & 0xF
            rm = instruction & 0xF
            rs = (instruction >> 8) & 0xF
            return "MUL", {'rd': rd, 'rm': rm, 'rs': rs}
        
        # BX instruction
        elif (instruction & 0x0FFFFFF0) == 0x012FFF10:
            rm = instruction & 0xF
            return "BX", {'rm': rm}

        elif instr_type == 0b00:
            # Data Processing instructions
            rn = (instruction >> 16) & 0xF
            rd = (instruction >> 12) & 0xF
            operand2 = instruction & 0xFFF

            if i_flag:  # Immediate
                imm = operand2
                if opcode == 0b1101:  # MOV
                    return "MOV_IMM", {'rd': rd, 'immediate': imm}
                elif opcode == 0b0100:  # ADD
                    return "ADD_IMM", {'rd': rd, 'rn': rn, 'immediate': imm}
                elif opcode == 0b0010:  # SUB
                    return "SUB_IMM", {'rd': rd, 'rn': rn, 'immediate': imm}
                elif opcode == 0b1010:  # CMP
                    return "CMP_IMM", {'rn': rn, 'immediate': imm}
                elif opcode == 0b0000:  # AND
                    return "AND_IMM", {'rd': rd, 'rn': rn, 'immediate': imm}
                elif opcode == 0b0001:  # EOR (XOR)
                    return "EOR_IMM", {'rd': rd, 'rn': rn, 'immediate': imm}
                elif opcode == 0b1100:  # ORR
                    return "ORR_IMM", {'rd': rd, 'rn': rn, 'immediate': imm}
                elif opcode == 0b1110:  # BIC (Bit Clear)
                    return "BIC_IMM", {'rd': rd, 'rn': rn, 'immediate': imm}
                elif opcode == 0b1111:  # MVN (Move NOT)
                    return "MVN_IMM", {'rd': rd, 'immediate': imm}
                elif opcode == 0b1000:  # TST (Test)
                    return "TST_IMM", {'rn': rn, 'immediate': imm}
                elif opcode == 0b1001:  # TEQ (Test Exclusive)
                    return "TEQ_IMM", {'rn': rn, 'immediate': imm}
            else:  # Register
                rm = instruction & 0xF
                if opcode == 0b1101:  # MOV
                    return "MOV", {'rd': rd, 'rm': rm}
                elif opcode == 0b0100:  # ADD
                    return "ADD", {'rd': rd, 'rn': rn, 'rm': rm}
                elif opcode == 0b0010:  # SUB
                    return "SUB", {'rd': rd, 'rn': rn, 'rm': rm}
                elif opcode == 0b1010:  # CMP
                    return "CMP", {'rn': rn, 'rm': rm}
                elif opcode == 0b0000:  # AND
                    return "AND", {'rd': rd, 'rn': rn, 'rm': rm}
                elif opcode == 0b0001:  # EOR (XOR)
                    return "EOR", {'rd': rd, 'rn': rn, 'rm': rm}
                elif opcode == 0b1100:  # ORR
                    return "ORR", {'rd': rd, 'rn': rn, 'rm': rm}
                elif opcode == 0b1110:  # BIC (Bit Clear)
                    return "BIC", {'rd': rd, 'rn': rn, 'rm': rm}
                elif opcode == 0b1111:  # MVN (Move NOT)
                    return "MVN", {'rd': rd, 'rm': rm}
                elif opcode == 0b1000:  # TST (Test)
                    return "TST", {'rn': rn, 'rm': rm}
                elif opcode == 0b1001:  # TEQ (Test Exclusive)
                    return "TEQ", {'rn': rn, 'rm': rm}

        elif instr_type == 0b01:
            # LDR/STR
            l_flag = (instruction >> 20) & 0x1
            rn = (instruction >> 16) & 0xF
            rd = (instruction >> 12) & 0xF
            offset = instruction & 0xFFF
            
            # For proper LDR/STR, we need to handle the base register
            if l_flag:
                return "LDR", {'rd': rd, 'rn': rn, 'offset': offset}
            else:
                return "STR", {'rd': rd, 'rn': rn, 'offset': offset}

        elif instr_type == 0b10:
            # Branch instructions
            link = (instruction >> 24) & 0x1
            offset = instruction & 0xFFFFFF
            # Sign-extend 24-bit offset
            if offset & 0x800000:
                offset -= 0x1000000
            if link:
                return "BL", {'offset': offset}
            else:
                return "B", {'offset': offset}

        return "UNKNOWN", {}