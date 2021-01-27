#!/usr/bin/env python3
import math
from flask import Flask, url_for, jsonify, render_template
from json2html import *

#aspirational - use pricing api
#import requests
#from bs4 import BeautifulSoup

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

def scale_data(data,inputs):
    data['scaler'] = 1 + inputs['scale']
    data['reads'] = math.ceil(inputs['reads'] * data['scaler'])
    data['writes'] = math.ceil(inputs['writes'] * data['scaler'])
    data['storage']  = math.ceil(inputs['storage'] * data['scaler'])
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
def ds_pricing(reads=30000, writes=20000, storage=100, scale=0.0):

    data={}
    inputs = get_input(reads,writes,storage,scale)
    data=scale_data(data,inputs)

    data['location'] = 'nam5'
    data['type'] = 'Global Managed ACID'
    data['storage_base_cost'] = 0.18
    data['storage_cost'] = data['storage_base_cost'] * data['storage'] * 1024 # TB to GB

    data['read_base_cost'] = 0.06
    data['write_base_cost'] = 0.18
    data['delete_base_cost'] = 0.02

    data['io_unit'] = 100000.0
    data['monthly_reads'] = data['reads'] * globals['seconds_to_month']
    data['monthly_writes'] = data['writes'] * globals['seconds_to_month']

    data['read_cost'] = data['monthly_reads'] / data['io_unit'] * data['read_base_cost']
    data['write_cost'] = data['monthly_writes']  / data['io_unit'] * data['write_base_cost']
    data['io_cost'] = data['read_cost'] + data['write_cost']
    data['total_cost'] = data['io_cost'] + data['storage_cost']
    
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

@app.route("/pricing/lp/json/<int:reads>/<int:writes>/<int:storage>/<float:scale>")
def lp_json_params(reads=30000, writes=20000, storage=100, scale=0.0):
    o1 = ds_pricing(reads,writes,storage,scale)['data']
    o2 = bt_pricing(reads,writes,storage,scale)['data']
    o3 = spanner_pricing(reads,writes,storage,scale)['data']
    output = { 'Datastore': o1, 'Bigtable': o2, 'Spanner' :o3} 
    return output

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
    o1 = json2html.convert(ds_pricing(reads,writes,storage,scale)['data'])
    o2 = json2html.convert(bt_pricing(reads,writes,storage,scale)['data'])
    o3 = json2html.convert(spanner_pricing(reads,writes,storage,scale)['data'])
    return o1 + o2 + o3
    #gh =json2html.convert(globals)

@app.route("/pricing/bt")
def __def_bt_pricing():
    return bt_pricing()

@app.route("/pricing/bt/<int:reads>/<int:writes>/<int:storage>/<float:scale>")
def bt_pricing(reads=30000, writes=20000, storage=100, scale=0.0):
     
    #multi region - 10K R/s, 10 W/s, 2.5 SSD per node
    config = { 
        'r':10000.0, 
        'w': 10000.0, 
        's': 2.5, 
        'rec_size': 1024, #record size in kb
        'rec_pct_chg': 0.002,  #saying that 500th of writen data actually results in a delta
        'replication_base_cost': [0.12,0.11,0.08],
        'storage_base_cost' : {'ssd' : 0.17 },
        'node_base_cost': 0.65,
        'location': 'us-central1,europe-west1'
        }
    data={}
    inputs = get_input(reads,writes,storage,scale)
    data=scale_data(data,inputs)
    data['type'] = 'M-S Repl, Eventual'
    data['clusters'] = 4
    calc_nodes(data,config)

    # set config to display 
    data['location'] = config['location']
    data['storage_base_cost'] = config['storage_base_cost']['ssd']            #0.17 #ssd
    data['storage_cost'] = data['storage_base_cost'] * data['storage'] * 1024 # TB to GB

    data['replicated_storage_cost'] = data['storage_cost'] * (data['clusters']  - 1 )          
    data['node_base_cost'] = config['node_base_cost']   #0.65 #per/hr
    data['node_cost'] = data['node_base_cost'] * data['nodes'] * 24 * 30
    data['total_cost_single_region'] = data['storage_cost']  + data['node_cost']

    # replication / network 
    # need dual regional clusters 
    data['replicated_data_size'] = math.ceil(data['monthly_writes'] * config['rec_size'] / 1024 / 1024 * config['rec_pct_chg']) #GBs
    app.logger.info('replicated data size %.2f', data['replicated_data_size']/1024.0)

    i = 1 if data['replicated_data_size']/1024.0 < 10 else 2 
    
    data['replication_base_cost'] = config['replication_base_cost'][i]
    
    data['replication_network_cost'] = data['replicated_data_size']  * data['replication_base_cost']

    # cluster+storage x2 + replicated changes
    data['total_cost'] = data['total_cost_single_region'] * data['clusters'] + data['replication_network_cost']
    format_data(data)
    output= {'inputs': inputs, 'globals':globals,'data': data, 'config': config}
    return output    

#refactor? probably need real classes...
def calc_nodes(data,c):
    # need to buffer nodes to not run out of IO on spikes or storage
    
    data['read_nodes_min']  = math.ceil(data['reads']  / c['r']) 
    data['write_nodes_min'] = math.ceil(data['writes'] / c['w'])
    data['storage_nodes_min'] = math.ceil(data['storage'] / c['s'] )
    n={k: v for k, v in data.items() if 'nodes_min' in k}
    (mk,mv)=sorted(n.items(),key=lambda x: (x[1]),reverse=True)[0]
    data['node_driver']=mk
    # 30% capacity or reads/writes but only 10% capacity for storage
    nf = 1.1 if 'storage' in mk else 1.3 
    data['nodes'] = int(mv * nf) 
    data['node_driver']=mk

    data['nodes_read_capacity'] = int(data['nodes'] * c['r'])
    data['nodes_write_capacity'] = int(data['nodes'] * c['w'])
    data['nodes_storage_capacity'] = int(data['nodes'] * c['s'])

    data['monthly_reads'] = data['reads'] * globals['seconds_to_month']
    data['monthly_writes'] = data['writes'] * globals['seconds_to_month']
   
@app.route("/pricing/spanner/")
def __def_spanner_pricing():
    return spanner_pricing()

@app.route("/pricing/spanner/<int:reads>/<int:writes>/<int:storage>/<float:scale>")
def spanner_pricing(reads=30000, writes=20000, storage=100, scale=0.1):

    # single-regions (3 zones)
    #config = { 'r': 10000.0, 'w': 2000.0, 's': 2.0}
    # multi-regions
    config = { 'multi': {'r': 7000.0, 'w': 1800.0, 's': 2.0},
               'single':{ 'r': 10000.0, 'w': 2000.0, 's': 2.0}
    }

    data={}
    data['type'] = 'Multi Region'
    data['location'] = 'nam3'
    data['clusters'] = 1

    inputs = get_input(reads,writes,storage,scale)
    data=scale_data(data,inputs)
    calc_nodes(data, config['multi'])
    
    data['storage_base_cost'] = 0.50
    data['storage_cost'] = data['storage_base_cost'] * data['storage'] * 1024 # TB to GB

    data['node_base_cost'] = 3.0
    data['node_cost'] = data['node_base_cost'] * data['nodes'] * 24 * 30
    data['total_cost'] =  data['storage_cost']  + data['node_cost']
    
    format_data(data)

    output= {'globals':globals,'data': data, 'config': config}
    return output

@app.route('/app/')
def webapp():
    return render_template('public/index.html')

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