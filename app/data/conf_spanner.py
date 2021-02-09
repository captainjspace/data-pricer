#!/usr/bin/env python3
config = {
    'global': {
        'clusters': 3,
        'reads_per_second': 7000.0,
        'writes_per_second': 1000.0,
        'storage_per_node_(TB)': 2.0,
        'node_base_cost': 9.0,
        'type': 'Global Transactional',
        'location': 'nam3',
        'storage_base_cost': 0.9,
        'node_overhead_factor': 2.0
    },
    'multi':  {
        'clusters': 2,
        'reads_per_second': 7000.0,
        'writes_per_second': 1800.0,
        'storage_per_node_(TB)': 2.0,
        'node_base_cost': 3.0,
        'type': 'Multi Region Transactional',
        'location': 'nam3',
        'storage_base_cost': 0.5,
        'node_overhead_factor': 2.0
    },
    'single': {
        'clusters': 1,
        'reads_per_second': 10000.0,
        'writes_per_second': 2000.0,
        'storage_per_node_(TB)': 2.0,
        'node_base_cost': 0.9,
        'type': 'Single Region Transactional',
        'location': 'us-central1',
        'storage_base_cost': 0.3,
        'node_overhead_factor': 1.5
    }
}
def get():
    return config
    
def main():
    print('{}'.format(config))

if __name__ == "__main__":
    main()
