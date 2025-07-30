#!/usr/bin/env python3
"""
CP216 - ARM/Thumb Simulator
Main entry point for the ARM/Thumb disassembler and simulator
Wilfrid Laurier University - Spring 2025
"""

import sys
from enhanced_executor import EnhancedARMExecutor
from cache import CacheSimulator, log_to_csv, plot_cache_costs

def print_banner():
    print("=" * 60)
    print("          CP216 ARMv7 Instruction Simulator")
    print("                Wilfrid Laurier University")
    print("                 Spring 2025 - Group 43")
    print("=" * 60)

def print_usage():
    print("\nUsage: python main.py")
    print("You will be prompted to enter one or more test files to run.")
    print("Example input: test_arm.txt test_loop.txt\n")

def run_simulation(filename):
    print(f"\nLoading program from: {filename}")

    # Define cache configuration
    l1i_conf = {"size": 1024, "block_size": 8, "mapping": "direct"}
    l1d_conf = {"size": 1024, "block_size": 8, "mapping": "direct"}
    l2_conf = {"size": 16384, "block_size": 32, "mapping": "direct"}
    cache = CacheSimulator(l1i_conf, l1d_conf, l2_conf)

    try:
        simulator = EnhancedARMExecutor(cache=cache)
        simulator.load_program_from_file(filename)
        print("Program loaded successfully!")

        print("\n" + "=" * 60)
        print("EXECUTION TRACE")
        print("=" * 60)

        simulator.execute_program()

        print("\n" + "=" * 60)
        print("FINAL STATE")
        print("=" * 60)

        simulator.display_state()

        summary = cache.summarize()
        log_to_csv("cache_results.csv", filename, 8, 8, 32, "direct", summary)

        print("\nCACHE SUMMARY:")
        print("-" * 40)
        for k, v in summary.items():
            print(f"{k.replace('_', ' ').title()}: {v}")

    except FileNotFoundError:
        print(f"\nError: File '{filename}' not found!")
    except Exception as e:
        print(f"\n[Runtime Error] {str(e)}")

def main():
    print_banner()
    print_usage()

    user_input = input("Enter test file(s) separated by spaces (or press Enter to use program.txt): ").strip()
    filenames = user_input.split() if user_input else ["program.txt"]

    for filename in filenames:
        run_simulation(filename)

    plot_cache_costs("cache_results.csv")

if __name__ == "__main__":
    main()
