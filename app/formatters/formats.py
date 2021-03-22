from math import floor

magnitudeDict={0:'', 1:'K', 2:'M', 3:'B', 4:'T'}

def simplify(num):
    num=floor(num)
    magnitude=0
    while num>=1000.0:
        magnitude+=1
        num=num/1000.0
    return(f'{floor(num*100.0)/100.0}{magnitudeDict[magnitude]}')





def format_data(data):
    """
    set up a config grid -- naming driving formatting
    'key': 'format' ... apply
    """

    # TODO Make Human readable big humnsd 500K, 1.2M 87B....
    #data =  {k:v for k,v in data.items() if not(isinstance(v,list)) and not(isinstance(v,dict))}

    #print(data)    

    number_fields = ['reads','writes','deletes', 'replicated_data_size','io_unit', 'monthly_reads', 'monthly_writes', 'monthly_deletes']
    numbers_units = {'nodes_read_capacity':'/ sec', 'nodes_write_capacity':'/ sec', 'nodes_storage_capacity':'(TB)', 'storage':'(TB)' }
    #money_fields  = []
    cost = { key:'${:,.2f}'.format(value) for key, value in data.items() if 'cost' in key }
    #for key in cost: del data[key]
  


    # acapacity fields -- clean this - fix data structure 
    capacity = { key:'{} {}'.format(simplify(value), numbers_units[key]) for key, value in data.items() if key in numbers_units.keys()}

    # general number fields
    numbers  = { key:'{}'.format(simplify(value)) for key, value in data.items() if key in number_fields }
    
    # data.update(cost)
    data.update(cost)
    data.update(capacity)
    data.update(numbers)

    return data