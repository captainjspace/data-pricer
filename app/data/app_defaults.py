#!/usr/bin/env python3

# maps to form submit from .js or curl, etc
default_inputs = {
    'ctype':'',
    'stype':'',
    'reads': 33000,
    'writes': 22000,
    'deletes': 0.0,
    'storage': 100,
    'scale': 0.0,
    'ioscale': 0.0,
    'disc_factor':1,
    'bt_discount_factor': 1,
    'ds_discount_factor': {'reads':1, 'writes':1, 'deletes':1, 'storage':1},
    'spanner_discount_factor': 1,
    'storage_type': 'ssd',
    'months':12,
    'years': 3
}

def process_inputs(**kwargs):
    o = {}
    o.update(default_inputs)
    for k,v in kwargs.items():
        o[k]=v
    return o   

def get(conf=default_inputs):
    o = {}
    o.update(conf)
    return o
    
def main():
    print('{}'.format(default_inputs))

if __name__ == "__main__":
    main()
