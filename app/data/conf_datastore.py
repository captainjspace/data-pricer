#!/usr/bin/env python3

tiered = {
    'free_reads': 50000,
    'free_writes': 20000,
    'free_deletes': 20000,
    'free_small_ops': 50000,
    'free_egress': 10 #GiB
}

config = {
    'single-region': {
        'location': 'us-west4',
        'type': 'Single Region Transactional',
        'storage_type': 'ssd',
        'read_base_cost': 0.033,
        'write_base_cost': 0.099,
        'delete_base_cost': 0.011,
        'storage_base_cost': 0.165,
        'tier1_cap': 50000,  # units
        'tier2_discount_factor': 0.85,  # 15% off
        'io_unit': 100000.0,
        'platform': tiered
    },
    'multi-region': {
        'location': 'nam5',
        'type': 'Managed Multi Region Transactional',
        'storage_type': 'ssd',
        'read_base_cost': 0.06,
        'write_base_cost': 0.18,
        'delete_base_cost': 0.02,
        'storage_base_cost': 0.18,
        'tier1_cap': 50000,  # units
        'tier2_discount_factor': 0.85,  # 15% off
        'io_unit': 100000.0,
        'platform': tiered
    }
}

def get():
    return config

def main():
    print('{}'.format(config))

if __name__ == "__main__":
    main()
