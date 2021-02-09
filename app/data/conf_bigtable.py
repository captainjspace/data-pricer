#!/usr/bin/env python3
config = {
    'repl-multi': {
        'clusters': 4,
        'reads_per_second': 10000.0,
        'writes_per_second': 10000.0,
        'storage_per_node_(TB)': 2.5,
        'type': 'Multi Replication Eventually Consistent',
        'rec_size': 1024,  # record size in kb
        'rec_pct_chg': 0.002,  # saying that 500th of writen data actually results in a delta
        'replication_base_cost': [0.12, 0.11, 0.08],
        'storage_base_cost': {'ssd': 0.17, 'hdd': 0.026},
        'node_base_cost': 0.65,
        'location': 'us-central1,europe-west1',
        'node_overhead_factor': 1.3
    },
    'repl-single': {
        'clusters': 2,
        'reads_per_second': 10000.0,
        'writes_per_second': 10000.0,
        'storage_per_node_(TB)': 2.5,
        'type': 'Single Replication Eventually Consistent',
        'storage_base_cost': {'ssd': 0.17, 'hdd': 0.026},
        'node_base_cost': 0.65,
        'location': 'us-central1,europe-west1',
        'rec_size': 1024,  # record size in kb
        'rec_pct_chg': 0.002,  # saying that 500th of writen data actually results in a delta
        'replication_base_cost': [0.12, 0.11, 0.08],
        'node_overhead_factor': 1.3
    },
    'single': {
        'clusters': 1,
        'reads_per_second': 10000.0,
        'writes_per_second': 10000.0,
        'storage_per_node_(TB)': 2.5,
        'type': 'Single Region Eventually Consistent',
        'storage_base_cost': {'ssd': 0.17, 'hdd': 0.026},
        'node_base_cost': 0.65,
        'location': 'us-central1',
        'rec_size': 1024,  # record size in kb
        'rec_pct_chg': 0.000,  # saying that 500th of writen data actually results in a delta
        'replication_base_cost': [0.12, 0.11, 0.08],
        'node_overhead_factor': 1.3
    }
}

def get():
    return config
    
def main():
    print('{}'.format(config))

if __name__ == "__main__":
    main()
