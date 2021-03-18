#!/usr/bin/env python3
import math, time
from flask import Flask, url_for, jsonify, render_template, request, json
from json2html import *

# local libraries
import log_config
from data import conf_bigtable, conf_spanner, conf_datastore, app_defaults, conf_global 
from formatters import formats

# aoplication fields
globals = conf_global.get()
version='v0.0.11'+'{}'.format(time.time())
app = Flask(__name__)


# worker functions find class homes ...

#Data method
# make this gen monthlies in to an annual
def scale_data(data,inputs):
    #app.logger.info('{}'.format(inputs))
    #data['scaler'] = 1 + inputs['scale']
    data['reads'] = math.ceil(inputs['reads'] * (1 + inputs['ioscale']) )
    data['writes'] = math.ceil(inputs['writes'] * (1+ inputs['ioscale']) )
    data['deletes'] = math.ceil(inputs['deletes'] * (1+ inputs['ioscale']) )
    data['storage']  = math.ceil(inputs['storage'] * (1+ inputs['scale']) )
    return data

#Formatter
def format_data(data):
    return formats.format_data(data)


@app.route("/pricing/ds_pricing/")
def __def_ds_pricing():
    return ds_pricing(app_defaults.get())


## Route original param route -- DEPRECATED
@app.route("/pricing/ds/<int:reads>/<int:writes>/<int:storage>/<float:scale>")
def ds_pricing(reads=30000, writes=20000, storage=100, scale=0.0, ctype='multi-region', disc_factor=app_defaults.get()['ds_discount_factor']):

    params = app_defaults.get()
    inputs = {
        'reads': reads,
        'writes': writes,
        'storage': storage,
        'scale':scale,
        'ctype':ctype,
        'disc_factor': disc_factor
    }
    params.update(inputs)
    return ds_pricing(params)

# Datastore Pricer
def ds_pricing(inputs):

    # refactor
    ctype = inputs['ctype']
    ctypes = conf_datastore.get().keys()  # ['single-region', 'multi-region']
    # if not provided or if invalid, select default
    if ctype is not None and ctype not in ctypes: ctype=ctypes[1] # issue warning? / default to multi

    # bs price config 
    cfg = conf_datastore.get()[ctype]
   
    data={}
    app.logger.debug('DS PRICING: CFG:{}'.format(json.dumps(cfg, indent=2)))
    app.logger.debug('DS INPUTS: CFG:{}'.format(json.dumps(inputs['disc_factor'], indent=2)))
    
    data=scale_data(data,inputs)
    # push config into data
    data.update(cfg)

    #validate sub discounts refactor
    app.logger.debug('TYPE DISCOUNT: {}'.format(type(inputs['disc_factor'])))
    if type(inputs['disc_factor']) is not dict:
        inputs['disc_factor']=app_defaults.get()['ds_discount_factor']

    data['storage_cost'] = data['storage_base_cost'] * data['storage'] * 1024 # TB to GB
    data['discounted_storage_cost'] = data['storage_cost'] * inputs['disc_factor']['storage']


    #adjust freebies, using 30 days ...
    data['monthly_reads'] = data['reads'] * globals['seconds_to_month'] - (30 * cfg['platform']['free_reads'])
    data['monthly_writes'] = data['writes'] * globals['seconds_to_month'] - (30 * cfg['platform']['free_writes'])
    data['monthly_deletes'] = max(0,data['deletes'] * globals['seconds_to_month'] - (30 * cfg['platform']['free_deletes']))


    #READS
    # default
    data['read_cost'] = data['monthly_reads'] / data['io_unit'] * data['read_base_cost']

    #adjust tiered discount -- almost always over 50K per day.
    if data['monthly_reads'] > data['tier1_cap'] * data['io_unit']:
        data['read_cost_tier1'] = data['tier1_cap'] * data['read_base_cost']
        data['read_cost_tier2'] = ( data['monthly_reads'] / data['io_unit'] - data['tier1_cap'] ) * data['read_base_cost']
        data['read_cost'] = data['read_cost_tier1'] + data['read_cost_tier2']
    
    # if discount...(default is 1) 
    data['discounted_read_cost'] = data['read_cost'] * inputs['disc_factor']['reads']

    # WRITES
    data['write_cost'] = data['monthly_writes']  / data['io_unit'] * data['write_base_cost']
    data['discounted_write_cost'] = data['write_cost'] * inputs['disc_factor']['writes']
 
    # DELETES
    data['delete_cost'] = data['monthly_deletes']  / data['io_unit'] * data['delete_base_cost']  ### fix me
    data['discounted_delete_cost'] = data['delete_cost'] * inputs['disc_factor']['deletes']

    # TOTAL IO
    data['io_cost'] = data['read_cost'] + data['write_cost'] + data['delete_cost']    
    data['discounted_io_cost'] = data['discounted_read_cost'] + data['discounted_write_cost'] + data['discounted_delete_cost']   

    # TOTAL COSTS
    data['total_cost'] = data['io_cost'] + data['storage_cost']
    data['total_discounted_cost'] = data['discounted_io_cost'] + data['discounted_storage_cost']

    format_data(data)
        
    output= {'inputs': inputs, 'globals': globals,'data': data, 'config': cfg}
    return output    


#TODO Abstract out request.data from below- so it functions off a dict
# add caller
# then add loop construct to build master data state of 12 monhts 3 years -- 
# integrated front end


@app.route("/pricing/lp/json/conf", methods=['POST'])
def lp_json_conf():

    # default input
    cfg = app_defaults.get()
    app.logger.info('App Defaults: {}'.format(cfg))

    # receive json input
    input_json = request.data
    app.logger.info('Posted Input: {}'.format(input_json))

    app.logger.debug(input_json, type(input_json))
    if input_json:
      json_input = json.loads(input_json)
      app.logger.info('Form Input:\n{}'.format(json.dumps(json_input, indent=2)))
      cfg.update(json_input)

    
    # function driver table
    measures = {
        'Datastore Multi': {'ctype': 'multi-region', 'discount': 'ds_discount_factor', 'funcname': ds_pricing, 'stype': 'ssd'},
        'Datastore Single': {'ctype': 'single-region', 'discount': 'ds_discount_factor', 'funcname': ds_pricing, 'stype': 'ssd'},
        'Bigtable Multi Replication': {'ctype': 'repl-multi', 'discount': 'bt_discount_factor', 'funcname': bt_pricing, 'stype': 'ssd'},
        'Bigtable Single Replication': {'ctype': 'repl-single', 'discount': 'bt_discount_factor', 'funcname': bt_pricing, 'stype': 'ssd'},
        'Bigtable Single SSD': {'ctype': 'single', 'discount': 'bt_discount_factor', 'funcname': bt_pricing, 'stype': 'ssd'},
        'Bigtable Single HDD': {'ctype': 'single', 'discount': 'bt_discount_factor', 'funcname': bt_pricing, 'stype': 'hdd'},
        'Spanner Multi': {'ctype': 'multi', 'discount': 'spanner_discount_factor', 'funcname': spanner_pricing, 'stype': 'ssd'},
        'Spanner Single': {'ctype': 'single', 'discount': 'spanner_discount_factor', 'funcname': spanner_pricing, 'stype': 'ssd'},
        'Spanner Global': {'ctype': 'global', 'discount': 'spanner_discount_factor', 'funcname': spanner_pricing, 'stype': 'ssd'}
    }
    #app.logger.info('Executions: {}'.format(measures))

    

    output={}
    for k,v in measures.items():
        # refactor -- but selecting which discount use, currently flat,needs to 1:set -- 
        # (done but needs to shift left)
        # function name effectively carries the discount var key ... 
        cfg['disc_factor']=cfg[v['discount']] #conf key
        cfg.update(v) #merge
        # set output key to deference to function, pass in merged config
        output[k]=v['funcname'](cfg)['data']

    return output    


#refactor
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


#refactor - formatter
@app.route("/pricing/lp/html")
def lp_html():
    return json2html.convert(lp_json_conf())

#refactor
@app.route("/pricing/lp/<int:reads>/<int:writes>/<int:storage>/<float:scale>")
def lp_pricing(reads=30000, writes=20000, storage=100, scale=0.0):
    o1 = json2html.convert(ds_pricing(rcfg['reads'],cfg['writes'],cfg['storage'],cfg['scale'])['data'])
    o2 = json2html.convert(bt_pricing(rcfg['reads'],cfg['writes'],cfg['storage'],cfg['scale'])['data'])
    o3 = json2html.convert(spanner_pricing(rcfg['reads'],cfg['writes'],cfg['storage'],cfg['scale'])['data'])
    return o1 + o2 + o3

#@test
@app.route("/pricing/bt")
def __def_bt_pricing():
    return bt_pricing(app_defaults.get())

# deprecated
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


# Pricing Big Table
def bt_pricing(inputs=None):     
    #multi region - 10K R/s, 10 W/s, 2.5 SSD per node

    ctype = inputs['ctype']
    stype = inputs['stype']
    # validate 
    ctypes = conf_bigtable.get().keys()  # ['single', 'repl-single', 'repl-multi' ]
    if ctype is not None and ctype not in ctypes: ctype=ctypes[0]
    # questionable
    stypes = conf_bigtable.get_base()['storage_base_cost'].keys()
    if stype is not None and stype not in stypes: stype=stypes[0]

    cfg = conf_bigtable.get()[ctype] #config[ctype]

   
    app.logger.debug("config: {}, storage: {}".format(ctype,stype))
    
    data={}
    data.update(cfg)

    #bt needs storage type
    data['storage_type']=stype
    data['storage_base_cost'] = cfg['storage_base_cost'][stype]    

    data=scale_data(data,inputs)    

    calc_node_capacity(data,cfg)

    data['storage_cost'] = data['storage_base_cost'] * data['storage'] * 1024 # TB to GB
    data['replicated_storage_cost'] = data['storage_cost'] * (data['clusters']  - 1 )          
    data['node_base_cost'] = cfg['node_base_cost']   #0.65 #per/hr
    data['node_cost'] = data['node_base_cost'] * data['nodes'] * globals['hours_per_month']
    data['total_cost_single_region'] = data['storage_cost']  + data['node_cost']

    # replication / network 
    # need dual regional clusters 
    data['record_size'] = inputs['record_size'] or cfg['record_size'] 
    data['replicated_data_size'] = math.ceil(data['monthly_writes'] * data['record_size'] / 1024 / 1024 * cfg['rec_pct_chg']) #GBs
    #app.logger.info('replicated data size %.2f', data['replicated_data_size']/1024.0)
    i = 1 if data['replicated_data_size']/1024.0 < 10 else 2 
    data['replication_base_cost'] = cfg['replication_base_cost'][i]

    data['replication_network_cost'] = 0
    if cfg['replication'] is True:
       data['replication_network_cost'] = data['replicated_data_size']  * data['replication_base_cost'] 

    # cluster+storage x2 + replicated changes
    data['total_cost'] = data['total_cost_single_region'] * data['clusters'] + data['replication_network_cost']
    data['total_discounted_cost'] = data['total_cost'] * inputs['disc_factor']

    format_data(data)
    output= {'inputs': inputs, 'globals':globals,'data': data, 'config': cfg}
    return output    

# Pricing common calc by ndoes

#refactor? 
def calc_node_capacity(data,cfg):

    # need to buffer nodes to not run out of IO on spikes or storage
    app.logger.debug('data:\n{}'.format(json.dumps(data, indent=2)))
    app.logger.debug('cfg:\n{}'.format(json.dumps(cfg, indent=2)))

    storage_buffer = data['storage_overhead_factor']  # config relocate add at least 15% storage overhead


    # this is the bare minimum calc
    data['read_nodes_min']  = math.ceil(data['reads'] / cfg['reads_per_second']) 
    data['write_nodes_min'] = math.ceil(data['writes'] /  cfg['writes_per_second'])
    data['storage_nodes_min'] = math.ceil(data['storage'] / cfg['storage_per_node_(TB)'] )

    data['read_nodes_req']  = math.ceil(data['reads'] * cfg['node_overhead_factor'] / cfg['reads_per_second']) 
    data['write_nodes_req'] = math.ceil(data['writes'] * cfg['node_overhead_factor']  /  cfg['writes_per_second'])
    data['storage_nodes_req'] = math.ceil(data['storage'] * cfg['storage_overhead_factor']  / cfg['storage_per_node_(TB)'] )


    # scaling nodes
    n={k: v for k, v in data.items() if 'nodes_req' in k}
    app.logger.debug('nodes:\n{}'.format(json.dumps(n, indent=2)))
    (mk,mv)=sorted(n.items(),key=lambda x: (x[1]),reverse=True)[0]
    # use storage buffer overhead by default else nodes...
    nf = storage_buffer if 'storage' in mk else data['node_overhead_factor'] 
    data['nodes'] = int(mv) #int(mv * nf) 
    data['node_driver']=mk.replace("_req","").replace("_"," ").title()

    data['nodes_read_capacity'] = int(data['nodes'] * cfg['reads_per_second'])
    data['nodes_write_capacity'] = int(data['nodes'] * cfg['writes_per_second'])
    data['nodes_storage_capacity'] = int(data['nodes'] * cfg['storage_per_node_(TB)'])

    data['monthly_reads'] = data['reads'] * globals['seconds_to_month']
    data['monthly_writes'] = data['writes'] * globals['seconds_to_month']
   
@app.route("/pricing/spanner/")
def __def_spanner_pricing():
    return spanner_pricing(app_defaults.get())


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
    
    # config type
    ctype  = inputs['ctype']
    ctypes = conf_spanner.get().keys()   #['single','multi','global']
    if ctype is not None and ctype not in ctypes: ctype=ctype[1]

    # spanner price config
    config = conf_spanner.get()
   
    #start loading spanner data
    data = {}

    data.update(config[ctype])
    data=scale_data(data,inputs)
    calc_node_capacity(data, config[ctype])
    
    data['storage_cost'] = data['storage_base_cost'] * data['storage'] * 1024 # TB to GB
    data['node_cost'] = data['node_base_cost'] * data['nodes'] * globals['hours_per_month']
    data['total_cost'] =  data['storage_cost']  + data['node_cost']
    data['total_discounted_cost'] = data['total_cost'] * inputs['disc_factor']

    format_data(data)

    output= {'globals':globals,'data': data, 'config': config, 'inputs': inputs}
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
