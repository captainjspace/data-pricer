#!/usr/bin/env python3
base = {
    'reads_per_second': 10000.0,
    'writes_per_second': 10000.0,
    'storage_per_node_(TB)': 2.5,
    'storage_base_cost': {'ssd': 0.17, 'hdd': 0.026},
    'replication_base_cost': [0.12, 0.11, 0.08],
    'record_size': 1024,  # record size in kb
    'rec_pct_chg': 0.002,  # saying that 500th of writen data actually results in a delta
    'node_base_cost': 0.65,
    'location': 'us-central1,europe-west1',
    'node_overhead_factor': 1.3,
    'storage_overhead_factor': 1.15,
    'replication' : True
}

# overrides per cluster type
config = {
    'repl-multi': {
        'clusters': 4,
        'type': 'Multi Replication Eventually Consistent',
    },
    'repl-single': {
        'clusters': 2,
        'type': 'Single Replication Eventually Consistent',
    },
    'single': {
        'clusters': 1,
        'type': 'Single Region Eventually Consistent',
        'location': 'us-central1',
        'replication' : False
    }
}

# static assembly
for k in config.keys():
    builder = {}
    builder.update(base)
    builder.update(config[k])
    config[k]=builder

def get_base():
    return base

def get():
    return config

def main():
    print('{}'.format(config))


if __name__ == "__main__":
    main()
