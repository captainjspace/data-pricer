#!/usr/bin/env python3


config = {
    'single': {
        'location': 'us-central1',
        'type': 'Single Region (HA) Transactional',
        'nodes': '2 (instances)',
        'rdbms': 'postgresql',
        'storage_type': 'ssd',
        'vCPU_base_cost': {'od': 0.0413, 'cud1': 0.03098, 'cud3': 0.01982},
        'memory_base_cost': {'od': 0.0070, 'cud1': 0.00525, 'cud3': 0.00336},
        'storage_base_cost': {'ssd': 0.17, 'hdd': 0.090, 'backup': 0.080},
        'ip_base_cost': 0.010,
        'egress_base_cost': {'same': 0, 'region': 0.12, 'interconnect': 0.05, 'internet': 0.19},
        'instance': {
            'max_cpu': 96,
            'max_memory': 624,  # GB
            'max_storage': 30 # TB
        },
        'license': {
            'Enterprise': 0.47,
            'Standard':	0.13,
            'Web': 0.01134,
            'Express':	0.00
        },
        #https://cloud.google.com/sql/pricing
        #https://blog.doit-intl.com/how-does-a-cloud-sql-database-scale-and-what-to-know-when-setting-one-up-c23c52fc9947
        'tps_factors': [
            [2,1250],[4,2500],[8,5000],[16,10000],[32,12000],[64,13000], [96,14000]
        ],
        'replication' : False
    }
}


def get():
    return config


def main():
    print('{}'.format(config))


if __name__ == "__main__":
    main()
