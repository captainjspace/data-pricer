#!/usr/bin/env python3

base = {
    'storage_per_node_(TB)': 2.0,
    'storage_overhead_factor': 1.15,
    'storage_type': 'ssd'
}

config = {
    'global': {
        'clusters': 3,
        'reads_per_second': 7000.0,
        'writes_per_second': 1000.0,
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
        'node_base_cost': 3.0,
        'type': 'Multi Region Transactional',
        'location': 'nam3',
        'storage_base_cost': 0.5,
        'node_overhead_factor': 1.7
    },
    'single': {
        'clusters': 1,
        'reads_per_second': 10000.0,
        'writes_per_second': 2000.0,
        'node_base_cost': 0.9,
        'type': 'Single Region Transactional',
        'location': 'us-central1',
        'storage_base_cost': 0.3,
        'node_overhead_factor': 1.5
    }
}

# static assembly
for k in config.keys():
    builder = {}
    builder.update(base)
    builder.update(config[k])
    config[k]=builder

def get():
    return config


def main():
    print('{}'.format(config))


if __name__ == "__main__":
    main()
