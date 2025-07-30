# cache.py

import csv
import os
import matplotlib.pyplot as plt
from collections import defaultdict

class CacheLine:
    def __init__(self):
        self.valid = False
        self.tag = None
        self.dirty = False

class BaseCache:
    def __init__(self, size, block_size, mapping="direct"):
        self.size = size
        self.block_size = block_size
        self.mapping = mapping
        self.num_blocks = size // block_size
        self.lines = [CacheLine() for _ in range(self.num_blocks)]
        self.accesses = 0
        self.hits = 0
        self.misses = 0
        self.write_backs = 0

    def get_index_and_tag(self, address):
        block_number = address // self.block_size
        if self.mapping == "direct":
            index = block_number % self.num_blocks
        else:  # fully associative (simulate as single set)
            index = 0
        tag = block_number
        return index, tag

    def access(self, address, is_write=False):
        self.accesses += 1
        index, tag = self.get_index_and_tag(address)
        line = self.lines[index]

        if line.valid and line.tag == tag:
            self.hits += 1
            if is_write:
                line.dirty = True
            return True  # hit

        # Miss: simulate write-back if dirty
        self.misses += 1
        if line.valid and line.dirty:
            self.write_backs += 1
            print(f"[CACHE] Write-back occurred for address 0x{address:08X}")


        # Replace with new block
        line.valid = True
        line.tag = tag
        line.dirty = is_write
        return False  # miss

    def reset_stats(self):
        self.accesses = self.hits = self.misses = self.write_backs = 0

class CacheSimulator:
    def __init__(self, l1i_conf, l1d_conf, l2_conf):
        self.L1I = BaseCache(**l1i_conf)
        self.L1D = BaseCache(**l1d_conf)
        self.L2 = BaseCache(**l2_conf)
        self.stats = defaultdict(int)

    def access_instruction(self, address):
        if not self.L1I.access(address, is_write=False):
            print(f"[CACHE] L1I miss for 0x{address:08X}")
            if not self.L2.access(address, is_write=False):
                print(f"[CACHE] L2 miss for 0x{address:08X}")
                self.stats['L2_miss'] += 1
            else:
                print(f"[CACHE] L2 hit  for 0x{address:08X}")
                self.stats['L2_hit'] += 1
            self.stats['L1I_miss'] += 1
        else:
            print(f"[CACHE] L1I hit  for 0x{address:08X}")
            self.stats['L1I_hit'] += 1

    def access_data(self, address, is_write):
        access_type = "write" if is_write else "read"

        if not self.L1D.access(address, is_write=is_write):
            print(f"[CACHE] L1D {access_type} miss for 0x{address:08X}")
            if not self.L2.access(address, is_write=is_write):
                print(f"[CACHE] L2 {access_type} miss for 0x{address:08X}")
                self.stats['L2_miss'] += 1
            else:
                print(f"[CACHE] L2 {access_type} hit  for 0x{address:08X}")
                self.stats['L2_hit'] += 1
            self.stats['L1D_miss'] += 1
        else:
            print(f"[CACHE] L1D {access_type} hit  for 0x{address:08X}")
            self.stats['L1D_hit'] += 1

    def summarize(self):
        print(f"[DEBUG] L1I Misses: {self.stats['L1I_miss']} | Hits: {self.stats['L1I_hit']}")
        print(f"[DEBUG] L1D Misses: {self.stats['L1D_miss']} | Hits: {self.stats['L1D_hit']}")
        print(f"[DEBUG] L2 Misses: {self.stats['L2_miss']} | WriteBacks: {self.L1I.write_backs + self.L1D.write_backs + self.L2.write_backs}")
        return {
            'L1_miss': self.stats['L1I_miss'] + self.stats['L1D_miss'],
            'L2_miss': self.stats['L2_miss'],
            'write_backs': self.L1I.write_backs + self.L1D.write_backs + self.L2.write_backs,
            'cost': 0.5 * (self.stats['L1I_miss'] + self.stats['L1D_miss']) +
                    self.stats['L2_miss'] +
                    self.L1I.write_backs + self.L1D.write_backs + self.L2.write_backs
        }


    def reset(self):
        self.stats.clear()
        self.L1I.reset_stats()
        self.L1D.reset_stats()
        self.L2.reset_stats()

def log_to_csv(filename, test_file, l1i_block, l1d_block, l2_block, mapping, summary):
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='') as csvfile:
        fieldnames = [
            'Test File', 'L1I Block', 'L1D Block', 'L2 Block', 'Mapping',
            'L1 Misses', 'L2 Misses', 'Write Backs', 'Cost'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow({
            'Test File': test_file,
            'L1I Block': l1i_block,
            'L1D Block': l1d_block,
            'L2 Block': l2_block,
            'Mapping': mapping,
            'L1 Misses': summary['L1_miss'],
            'L2 Misses': summary['L2_miss'],
            'Write Backs': summary['write_backs'],
            'Cost': summary['cost']
        })

def plot_cache_costs(csv_file):
    import pandas as pd
    df = pd.read_csv(csv_file)

    # Group by 'Test File' and take average cost if duplicates exist
    df_grouped = df.groupby(['Test File', 'L1I Block'], as_index=False).mean(numeric_only=True)

    # Pivot cleanly after deduplication
    pivot = df_grouped.pivot(index='Test File', columns='L1I Block', values='Cost')
    pivot.plot(kind='bar', title="Cache Cost by L1I Block Size")
    plt.ylabel("Cost")
    plt.tight_layout()
    plt.show()
