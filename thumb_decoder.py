# ================================================================
# FILE: thumb_decoder.py
# DESCRIPTION: Decodes 16-bit Thumb instructions into (type, operands)
# ================================================================

class FixedThumbDecoder:
    """Decoder for 16-bit ARM Thumb instructions"""

    def __init__(self):
        self.registers = {
            0: 'R0', 1: 'R1', 2: 'R2', 3: 'R3',
            4: 'R4', 5: 'R5', 6: 'R6', 7: 'R7',
            8: 'R8', 9: 'R9', 10: 'R10', 11: 'R11',
            12: 'R12', 13: 'SP', 14: 'LR', 15: 'PC'
        }

    def decode_thumb_instruction(self, instruction, address=0):
        bits_15_13 = (instruction >> 13) & 0b111
        bits_15_11 = (instruction >> 11) & 0b11111
        bits_15_10 = (instruction >> 10) & 0b111111

        if bits_15_13 == 0b001:
            # Format 3: MOV/CMP/ADD/SUB Immediate
            op = (instruction >> 11) & 0x3
            rd = (instruction >> 8) & 0x7
            imm8 = instruction & 0xFF
            op_types = ['T_MOV_IMM', 'T_CMP_IMM', 'T_ADD_IMM', 'T_SUB_IMM']
            return op_types[op], {'rd': rd, 'immediate': imm8}

        elif bits_15_11 == 0b00011:
            # Format 2: ADD/SUB (register or immediate)
            is_imm = (instruction >> 10) & 0x1
            op = (instruction >> 9) & 0x1
            rn = (instruction >> 6) & 0x7
            rs = (instruction >> 3) & 0x7
            rd = instruction & 0x7
            if is_imm:
                return ('T_SUB_IMM' if op else 'T_ADD_IMM'), {'rd': rd, 'rs': rs, 'immediate': rn}
            else:
                return ('T_SUB' if op else 'T_ADD'), {'rd': rd, 'rs': rs, 'rn': rn}

        elif bits_15_13 == 0b000:
            # Format 1: Move shifted register
            shift_type = (instruction >> 11) & 0x3
            offset = (instruction >> 6) & 0x1F
            rs = (instruction >> 3) & 0x7
            rd = instruction & 0x7
            shift_ops = ['LSL', 'LSR', 'ASR']
            return f"T_{shift_ops[shift_type]}", {'rd': rd, 'rs': rs, 'offset': offset}

        elif bits_15_10 == 0b010000:
            # Format 4: ALU operations
            alu_op = (instruction >> 6) & 0xF
            rs = (instruction >> 3) & 0x7
            rd = instruction & 0x7
            alu_ops = [
                'AND', 'EOR', 'LSL', 'LSR', 'ASR', 'ADC', 'SBC', 'ROR',
                'TST', 'NEG', 'CMP', 'CMN', 'ORR', 'MUL', 'BIC', 'MVN'
            ]
            return f"T_{alu_ops[alu_op]}", {'rd': rd, 'rs': rs}

        elif bits_15_10 == 0b010001:
            # Format 5: Hi register ops / BX
            op = (instruction >> 8) & 0x3
            h1 = (instruction >> 7) & 0x1
            h2 = (instruction >> 6) & 0x1
            rs = ((h2 << 3) | ((instruction >> 3) & 0x7))
            rd = ((h1 << 3) | (instruction & 0x7))
            op_types = ['T_ADD', 'T_CMP', 'T_MOV_HI', 'T_BX']
            return op_types[op], {'rd': rd, 'rs': rs}
        
        elif bits_15_13 == 0b010:
            # Format 6/7/8: LDR/STR
            bits_12_11 = (instruction >> 11) & 0b11
            
            if bits_12_11 == 0b00:
                # Format 7: STR register
                rm = (instruction >> 6) & 0x7
                rb = (instruction >> 3) & 0x7
                rd = instruction & 0x7
                return "T_STR_REG", {'rd': rd, 'rb': rb, 'rm': rm}
            elif bits_12_11 == 0b01:
                # Format 7: STRH register
                rm = (instruction >> 6) & 0x7
                rb = (instruction >> 3) & 0x7
                rd = instruction & 0x7
                return "T_STRH_REG", {'rd': rd, 'rb': rb, 'rm': rm}
            elif bits_12_11 == 0b10:
                # Format 7: STRB register
                rm = (instruction >> 6) & 0x7
                rb = (instruction >> 3) & 0x7
                rd = instruction & 0x7
                return "T_STRB_REG", {'rd': rd, 'rb': rb, 'rm': rm}
            elif bits_12_11 == 0b11:
                # Format 6: LDR immediate (word-aligned)
                rd = (instruction >> 8) & 0x7
                offset = instruction & 0xFF
                return "T_LDR_PC", {'rd': rd, 'offset': offset}
        
        elif bits_15_13 == 0b011:
            # Format 9: LDR/STR immediate offset
            l_bit = (instruction >> 11) & 0x1
            offset = (instruction >> 6) & 0x1F
            rb = (instruction >> 3) & 0x7
            rd = instruction & 0x7
            
            if l_bit:
                return "T_LDR", {'rd': rd, 'rb': rb, 'offset': offset}
            else:
                return "T_STR", {'rd': rd, 'rb': rb, 'offset': offset}

        elif (instruction >> 12) == 0b1101 and ((instruction >> 8) & 0xF) != 0xF:
            # Format 16: Conditional branch
            condition = (instruction >> 8) & 0xF
            offset = instruction & 0xFF
            if offset & 0x80:
                offset -= 0x100  # sign extend
            return "T_BCC", {'condition': condition, 'offset': offset * 2}

        elif (instruction >> 11) == 0b11100:
            # Format 18: Unconditional branch
            offset = instruction & 0x7FF
            if offset & 0x400:
                offset -= 0x800  # sign extend
            return "T_B", {'offset': offset * 2}

        elif (instruction & 0xFF00) == 0xDF00:
            # Format 17: SWI
            imm8 = instruction & 0xFF
            return "T_SWI", {'immediate': imm8}

        else:
            return "T_UNKNOWN", {'raw': instruction}
