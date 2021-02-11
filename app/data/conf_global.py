#!/usr/bin/env python3


# refactor -- overlapping with new datastore config.  deprecated mostly
global_dict ={
  'read-from-api-complete': False,
  'hours_per_month': 730,
  'seconds_to_days' : 86400,
  'seconds_to_month' : 60 * 60 * 730,
  'core_fee':40.0,
  'subscription_retention_fee':0.27,
  'snapshot_fee':0.27,
  'retention_term':7, # max days on queue
  'free':10, #10TB free
  'task_rates':0.40, # per million over 5 billion
  'datastore': {
    'reads': 0.036, # per 100K,
    'writes': 0.108,
    'deletes': 0.012,
    'storage': 0.108, # per GiB per month  
    'read-quota': 50000,
    'write-quota': 20000,
    'delete-quota' :20000,
    'storage-quota' : 1 * 1024 * 1024 #1gb

  },
  'scaling' : .1
}


units = {
    'XB':2**30,
    'PB': 2**20,
    'TB': 2**10,
    'GB': 1,
    'MB': 1/2**10,
    'KB': 1/2**20,
    'B': 1/2**30
}

def get_units():
    return get(units)

def get(gset=global_dict):
    g = {}
    g.update(gset)
    return g
    
def main():
    print('{}'.format(get()))

if __name__ == "__main__":
    main()
