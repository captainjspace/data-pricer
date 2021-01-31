#!/usr/bin/env python3
import math,json
from flask import Flask, url_for, jsonify, render_template, request
from json2html import *


#aspirational - use pricing api
#import requests
#from bs4 import BeautifulSoup

version='v0.0.7'

#logger
from logging.config import dictConfig
dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s : %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})

app = Flask(__name__)


globals={
  'read-from-api-complete': False,
  'seconds_to_days' : 86400,
  'seconds_to_month' : 60 * 60 * 24 * 30,
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




@app.route("/pricing/ds_pricing/")
def __def_ds_pricing():
    return ds_pricing()

# refactor this is junky 
def get_input(reads=30000, writes=20000, storage=100, scale=0.0):
    inputs = {}
    inputs['reads']   = reads 
    inputs['writes']  = writes 
    inputs['storage'] = storage 
    inputs['scale']   = scale 
    return inputs

# make this gen monthlies in to an annual
def scale_data(data,inputs,):
    app.logger.info('{}'.format(inputs))
    #data['scaler'] = 1 + inputs['scale']
    data['reads'] = math.ceil(inputs['reads'] * (1 + inputs['ioscale']) )
    data['writes'] = math.ceil(inputs['writes'] * (1+ inputs['ioscale']) )
    data['storage']  = math.ceil(inputs['storage'] * (1+ inputs['scale']) )
    return data

def format_data(data):
    """
    set up a config grid -- naming driving formatting
    'key': 'format' ... apply
    """
    number_fields = ['reads','writes','replicated_data_size','io_unit']

    cost     = { key:'${:,.2f}'.format(value) for key, value in data.items() if 'cost' in key }
    capacity = { key:'{:,} / sec'.format(value) for key, value in data.items() if key in ['nodes_read_capacity','nodes_write_capacity']}
    numbers  = { key:'{:,.0f}'.format(value) for key, value in data.items() if 'monthly' in key or key in number_fields }
    data['storage']= '{:,} (TB)'.format(data['storage'])
    if 'nodes_storage_capacity' in data:
        data['nodes_storage_capacity']= '{:,} (TB)'.format(data['nodes_storage_capacity'])
    data.update(cost)
    data.update(capacity)
    data.update(numbers)

    return data

@app.route("/pricing/ds/<int:reads>/<int:writes>/<int:storage>/<float:scale>")
def ds_pricing(reads=30000, writes=20000, storage=100, scale=0.0, ctype='multi-region', disc_factor=0.85):
    params= {
        'reads': reads,
        'writes': writes,
        'storage': storage,
        'scale':scale,
        'ctype':ctype,
        'disc_factor': disc_factor,
        'ioscale':0.0,
        'months':12,
        'years': 3
    }
    return ds_pricing(params)

   
def ds_pricing(inputs):

    ctype = inputs['ctype']
    ctypes = ['single-region', 'multi-region']
    if ctype is not None and ctype not in ctypes: ctype=ctypes[1]

    # https://cloud.google.com/datastore/pricing
    config= {
        'single-region' : {
            'location': 'us-west4', 
            'type':'Single Region Transactional',
            'storage_type':'ssd',
            'read_base_cost':0.033, 
            'write_base_cost':0.099, 
            'delete_base_cost': 0.011,
            'storage_base_cost': 0.165,
            'tier1_cap': 50000, #units
            'tier2_discount_factor': 0.85 ,#15% off
            'io_unit': 100000.0,
        },
        'multi-region'  : {
            'location': 'nam5', 
            'type':'Managed Multi Region Transactional',
            'storage_type':'ssd',
            'read_base_cost':0.06, 
            'write_base_cost':0.18, 
            'delete_base_cost': 0.02,
            'storage_base_cost': 0.18,
            'tier1_cap': 50000, #units
            'tier2_discount_factor': 0.85, #15% off
            'io_unit': 100000.0,
        }
    }

    data={}
    #cfg = config[ctype]
    app.logger.info(config[ctype])
    
    #inputs = get_input(reads,writes,storage,scale)
    scale_data(data,inputs)

    # push config into data
    data.update(config[ctype])

    data['storage_cost'] = data['storage_base_cost'] * data['storage'] * 1024 # TB to GB
    data['monthly_reads'] = data['reads'] * globals['seconds_to_month']
    data['monthly_writes'] = data['writes'] * globals['seconds_to_month']
    
    data['read_cost'] = data['monthly_reads'] / data['io_unit'] * data['read_base_cost']
    if data['monthly_reads'] > data['tier1_cap'] * data['io_unit']:
        data['read_cost_tier1'] = data['tier1_cap'] * data['read_base_cost']
        data['read_cost_tier2'] = ( data['monthly_reads'] / data['io_unit'] - data['tier1_cap'] ) * data['read_base_cost']
        data['read_cost'] = data['read_cost_tier1'] + data['read_cost_tier2']
    #data['read_cost'] = data['monthly_reads'] / data['io_unit'] * data['read_base_cost']

    data['write_cost'] = data['monthly_writes']  / data['io_unit'] * data['write_base_cost']
    data['io_cost'] = data['read_cost'] + data['write_cost']
    
    data['total_cost'] = data['io_cost'] + data['storage_cost']
    data['total_discounted_cost']= data['total_cost'] * inputs['disc_factor']
    
    format_data(data)
    
    
    output= {'inputs': inputs, 'globals': globals,'data': data}
    return output    

@app.route("/pricing/lp/json")
def lp_json():
    o1 = ds_pricing()['data']
    o2 = bt_pricing()['data']
    o3 = spanner_pricing()['data']
    output = { 'globals' :globals , 'datastore': o1, 'bigtable': o2, 'spanner' :o3} 
    return output 

@app.route("/pricing/lp/json/conf", methods=['POST'])
def lp_json_conf():

    app.logger.info('POSTED:{}'.format(request.data))

    measures = {
        'Datastore Multi': {'ctype': 'multi-region', 'discount': 'ds_discount_factor', 'funcname': ds_pricing, 'stype': 'ssd'},
        'Datastore Single': {'ctype': 'single-region', 'discount': 'ds_discount_factor', 'funcname': ds_pricing, 'stype': 'ssd'},
        'Bigtable Multi Replication': {'ctype': 'repl-multi', 'discount': 'bt_discount_factor', 'funcname': bt_pricing, 'stype': 'ssd'},
        'Bigtable Single Replication': {'ctype': 'repl-single', 'discount': 'bt_discount_factor', 'funcname': bt_pricing, 'stype': 'ssd'},
        'Bigtable Single': {'ctype': 'single', 'discount': 'bt_discount_factor', 'funcname': bt_pricing, 'stype': 'hdd'},
        'Spanner Multi': {'ctype': 'multi', 'discount': 'bt_discount_factor', 'funcname': spanner_pricing, 'stype': 'ssd'},
        'Spanner Single': {'ctype': 'single', 'discount': 'bt_discount_factor', 'funcname': spanner_pricing, 'stype': 'ssd'},
        'Spanner Global': {'ctype': 'global', 'discount': 'bt_discount_factor', 'funcname': spanner_pricing, 'stype': 'ssd'}
    }
    cfg = {
        'reads': 30000,
        'writes': 20000,
        'storage': 100,
        'scale': 0.0,
        'ioscale': 0.0,
        'bt_discount_factor': 0.85,
        'ds_discount_factor': 0.75,
        'spanner_discount_factor': 0.70,
        'storage_type': 'ssd'
    }

    form = json.loads(request.data)
    cfg.update(form)

    output={}
    for k,v in measures.items():
        cfg['disc_factor']=cfg[v['discount']]
        cfg.update(v)
        output[k]=v['funcname'](cfg)['data']
    return output    
    
    # return {
    
    #   'Datastore Multi' : ds_pricing(cfg)['data'],
    #   'Datastore Single' : ds_pricing(cfg)['data'],
    #   'Bigtable Multi Replication': bt_pricing(cfg)['data'],
    #   'Bigtable Single Replication': bt_pricing(cfg)['data'],
    #   'Bigtable Single': bt_pricing(cfg)['data'],
    #   'Spanner Multi': spanner_pricing(cfg)['data'],
    #   'Spanner Single': spanner_pricing(cfg)['data'],
    #   'Spanner Global': spanner_pricing(cfg)['data']

    # }

@app.route("/pricing/lp/json/<int:reads>/<int:writes>/<int:storage>/<float:scale>")
def lp_json_params(reads=30000, writes=20000, storage=100, scale=0.0):
    return {

      'Datastore Multi' : ds_pricing(cfg['reads'],cfg['writes'],cfg['storage'],cfg['scale'])['data'],
      'Datastore Single' : ds_pricing(cfg['reads'],cfg['writes'],cfg['storage'],cfg['scale'],'single-region')['data'],
      'Bigtable Multi Replication': bt_pricing(cfg['reads'],cfg['writes'],cfg['storage'],cfg['scale'])['data'],
      'Bigtable Single Replication': bt_pricing(cfg['reads'],cfg['writes'],cfg['storage'],cfg['scale'], 'repl-single')['data'],
      'Bigtable Single': bt_pricing(cfg['reads'],cfg['writes'],cfg['storage'],cfg['scale'],'single', 'hdd')['data'],
      'Spanner Multi': spanner_pricing(cfg['reads'],cfg['writes'],cfg['storage'],cfg['scale'])['data'],
      'Spanner Single': spanner_pricing(cfg['reads'],cfg['writes'],cfg['storage'],cfg['scale'],'single')['data'],
      'Spanner Global': spanner_pricing(cfg['reads'],cfg['writes'],cfg['storage'],cfg['scale'],'global')['data']
    }
    #output = { 'Datastore': o1, 'Bigtable': o2, 'Spanner' :o3} 
    #return output

@app.route("/pricing/lp/html")
def lp_html():
    o1 = json2html.convert(ds_pricing()['data'])
    o2 = json2html.convert(bt_pricing()['data'])
    o3 = json2html.convert(spanner_pricing()['data'])
    gh =json2html.convert(globals)
    #output = { 'globals' :globals , 'datastore': o1, 'bigtable': o2, 'spanner' :o3} 
    #html = json2html.convert(output)
    return o1 + o2 + o3

@app.route("/pricing/lp/<int:reads>/<int:writes>/<int:storage>/<float:scale>")
def lp_pricing(reads=30000, writes=20000, storage=100, scale=0.0):
    o1 = json2html.convert(ds_pricing(rcfg['reads'],cfg['writes'],cfg['storage'],cfg['scale'])['data'])
    o2 = json2html.convert(bt_pricing(rcfg['reads'],cfg['writes'],cfg['storage'],cfg['scale'])['data'])
    o3 = json2html.convert(spanner_pricing(rcfg['reads'],cfg['writes'],cfg['storage'],cfg['scale'])['data'])
    return o1 + o2 + o3
    #gh =json2html.convert(globals)

@app.route("/pricing/bt")
def __def_bt_pricing():
    return bt_pricing()

@app.route("/pricing/bt/<int:reads>/<int:writes>/<int:storage>/<float:scale>")
def bt_pricing(reads=30000, writes=20000, storage=100, scale=0.0,ctype='repl-multi',stype='ssd',disc_factor=0.85):
    params= {
        'reads': reads,
        'writes': writes,
        'storage': storage,
        'scale': scale,
        'ctype': ctype,
        'disc_factor': disc_factor,
        'ioscale': 0.0,
        'months': 12,
        'years': 3
    }
    return bt_pricing(params)



def bt_pricing(inputs=None):     
    #multi region - 10K R/s, 10 W/s, 2.5 SSD per node

    ctype = inputs['ctype']
    stype = inputs['stype']
    #valid
    ctypes = ['single', 'repl-single', 'repl-multi' ]
    if ctype is not None and ctype not in ctypes: ctype=ctype[2]
    stypes = ['ssd','hdd']
    if stype is not None and stype not in stypes: stypes=stypes[0]

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

    app.logger.info("config: {}, storage: {}".format(ctype,stype))
    cfg = config[ctype]
    data={}
    #inputs = get_input(reads,writes,storage,scale)
    data.update(config[ctype])

    # storage type
    data['storage_type']=stype
    data['storage_base_cost'] = cfg['storage_base_cost'][stype]    


    data=scale_data(data,inputs)    
    calc_nodes(data,cfg)

    data['storage_cost'] = data['storage_base_cost'] * data['storage'] * 1024 # TB to GB
    data['replicated_storage_cost'] = data['storage_cost'] * (data['clusters']  - 1 )          
    data['node_base_cost'] = cfg['node_base_cost']   #0.65 #per/hr
    data['node_cost'] = data['node_base_cost'] * data['nodes'] * 24 * 30
    data['total_cost_single_region'] = data['storage_cost']  + data['node_cost']

    # replication / network 
    # need dual regional clusters 
    data['replicated_data_size'] = math.ceil(data['monthly_writes'] * cfg['rec_size'] / 1024 / 1024 * cfg['rec_pct_chg']) #GBs
    #app.logger.info('replicated data size %.2f', data['replicated_data_size']/1024.0)
    i = 1 if data['replicated_data_size']/1024.0 < 10 else 2 
    data['replication_base_cost'] = cfg['replication_base_cost'][i]

    data['replication_network_cost'] = data['replicated_data_size']  * data['replication_base_cost']

    # cluster+storage x2 + replicated changes
    data['total_cost'] = data['total_cost_single_region'] * data['clusters'] + data['replication_network_cost']
    data['total_discounted_cost'] = data['total_cost'] * inputs['disc_factor']

    format_data(data)
    output= {'inputs': inputs, 'globals':globals,'data': data, 'config': cfg}
    return output    

#refactor? probably need real classes...
def calc_nodes(data,c):
    # need to buffer nodes to not run out of IO on spikes or storage
    app.logger.info(data['reads']  , c)
    #data['storage_type'] = 'ssd' if c['storage_base_cost'][stype]

    data['read_nodes_min']  = math.ceil(data['reads'] / c['reads_per_second']) 
    data['write_nodes_min'] = math.ceil(data['writes'] /  c['writes_per_second'])
    data['storage_nodes_min'] = math.ceil(data['storage'] / c['storage_per_node_(TB)'] )
    n={k: v for k, v in data.items() if 'nodes_min' in k}
    (mk,mv)=sorted(n.items(),key=lambda x: (x[1]),reverse=True)[0]
    data['node_driver']=mk
    # 30% capacity or reads/writes but only 10% capacity for storage
    nf = 1.1 if 'storage' in mk else data['node_overhead_factor'] 
    data['nodes'] = int(mv * nf) 
    data['node_driver']=mk.replace("_min","")

    data['nodes_read_capacity'] = int(data['nodes'] * c['reads_per_second'])
    data['nodes_write_capacity'] = int(data['nodes'] * c['writes_per_second'])
    data['nodes_storage_capacity'] = int(data['nodes'] * c['storage_per_node_(TB)'])

    data['monthly_reads'] = data['reads'] * globals['seconds_to_month']
    data['monthly_writes'] = data['writes'] * globals['seconds_to_month']
   
@app.route("/pricing/spanner/")
def __def_spanner_pricing():
    return spanner_pricing()


@app.route("/pricing/spanner/<int:reads>/<int:writes>/<int:storage>/<float:scale>")
def spanner_pricing(reads=30000, writes=20000, storage=100, scale=0.1, ctype='multi',disc_factor=0.85):
    params= {
        'reads': reads,
        'writes': writes,
        'storage': storage,
        'scale':scale,
        'ctype':ctype,
        'disc_factor': disc_factor,
        'ioscale':0.0,
        'months':12,
        'years': 3
    }
    return spanner_pricing(params)

def spanner_pricing(inputs):
    # single-regions (3 zones)
    #config = { 'r': 10000.0, 'w': 2000.0, 's': 2.0}
    # multi-regions
    ctype  = inputs['ctype']
    ctypes = ['single','multi','global']
    if ctype is not None and ctype not in ctypes: ctype='multi'

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

    data = {
        'storage_type': 'ssd'
    }

    data.update(config[ctype])

    # data['type'] = config[ctype]['type']
    # data['location'] = config[ctype]['location']
    # data['storage_base_cost'] = config[ctype]['sc']

    #inputs = get_input(reads,writes,storage,scale)
    data=scale_data(data,inputs)
    calc_nodes(data, config[ctype])
    
    data['storage_cost'] = data['storage_base_cost'] * data['storage'] * 1024 # TB to GB
    data['node_cost'] = data['node_base_cost'] * data['nodes'] * 24 * 30
    data['total_cost'] =  data['storage_cost']  + data['node_cost']
    data['total_discounted_cost'] = data['total_cost'] * inputs['disc_factor']

    format_data(data)

    output= {'globals':globals,'data': data, 'config': config}
    return output

@app.route('/app/')
def webapp():
    return render_template('public/index.html', githash=version)

@app.route('/')
def index():
    return site_map()

def has_no_empty_params(rule):
    defaults = rule.defaults if rule.defaults is not None else ()
    arguments = rule.arguments if rule.arguments is not None else ()
    return len(defaults) >= len(arguments)

@app.route("/site-map/<o_format>")
def site_map(o_format='html'):
    o_formats=['html','json']
    if o_format in o_formats: 
        fmt=o_format
    links = []
    for rule in app.url_map.iter_rules():
        # Filter out rules we can't navigate to in a browser
        # and rules that require parameters
        if "GET" in rule.methods and has_no_empty_params(rule):
            url = url_for(rule.endpoint, **(rule.defaults or {}))
            links.append((url, rule.endpoint))
    # links is now a list of url, endpoint tuples
    return weblinks(links, fmt)
# END https://stackoverflow.com/questions/13317536/get-list-of-all-routes-defined-in-the-flask-app

def weblinks(links,format='html'):
    if format == 'json': return jsonify(links)
    link_text='<li><a href="{0}"> {1}</a></li>'
    op=" "
    for t in links:
        print(t)
        op = op + link_text.format(t[0],t[1])
    return op

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)
