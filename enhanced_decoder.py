import sys
from thumb_decoder import FixedThumbDecoder
from ARM_decoder import ARMDecoder

class EnhancedARMDecoder:
    """
    Combines ARM and Thumb instruction decoding into a unified interface
    """

    def __init__(self):
        self.arm_decoder = ARMDecoder()
        self.thumb_decoder = FixedThumbDecoder()
        self.mode = "ARM"  # default
        
    def set_mode(self, mode):
        """Set current instruction decoding mode"""
        if mode not in ["ARM", "Thumb"]:
            raise ValueError("Invalid mode. Must be 'ARM' or 'Thumb'")
        self.mode = mode
        
    def decode_instruction(self, instruction, address, mode=None):
        """Decode based on current or provided mode"""
        mode = mode or self.mode
        if mode == "ARM":
            return self.arm_decoder.decode_instruction(instruction, address)
        elif mode == "Thumb":
            return self.thumb_decoder.decode_thumb_instruction(instruction, address)
        return "UNKNOWN", {}
    
    def decode_thumb_instruction(self, instruction, address=0):
        return self.thumb_decoder.decode_thumb_instruction(instruction, address)


    def read_hex_text_file_mixed(self, filename):
        instructions = []
        addresses = []
        modes = []
        current_address = 0
        current_mode = "ARM"  # ADD THIS LINE - Initialize default mode

        with open(filename, 'r') as file:
            for line in file:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # Check for mode directives
                if line.upper() == "# ARM MODE":
                    current_mode = "ARM"
                    continue
                elif line.upper() == "# THUMB MODE":
                    current_mode = "THUMB"  # Change from "Thumb" to "THUMB" for consistency
                    continue

                try:
                    instr_value = int(line, 16)
                    instructions.append(instr_value)
                    addresses.append(current_address)
                    modes.append(current_mode)
                    current_address += 4 if current_mode == "ARM" else 2
                except ValueError:
                    print(f"Warning: Skipping invalid instruction line: {line}")

        return instructions, addresses, modes

    def decode_instruction(self, instruction, address, mode="ARM"):
        if mode == "ARM":
            return self.arm_decoder.decode_instruction(instruction, address)
        elif mode == "THUMB":
            return self.thumb_decoder.decode_thumb_instruction(instruction, address)
        else:
            return "UNKNOWN MODE"
