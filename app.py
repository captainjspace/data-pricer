#!/usr/bin/env python3
import math
from flask import Flask, url_for, jsonify, render_template
from bs4 import BeautifulSoup
import requests
from json2html import *

app = Flask(__name__)


# https://cloud.google.com/pubsub/pricing#example-subscription-with-retained-acknowledged-messages
# https://cloud.google.com/skus?currency=USD&filter=pub#sku-pubsub
# https://en.wikipedia.org/wiki/Tebibyte
# https://cloud.google.com/pubsub/docs/reference/rest/v1/Snapshot#:~:text=Its%20exact%20lifetime%20is%20determined,unacked%20message%20in%20the%20subscription)%20.



######################################################################################
#                               MESSAGE DELIVERY BASIC                               #
#                                   027D-B6C7-CCA2                                   #
# 0.00 USD (FREE) PER TEBIBYTE, FOR 0 TO 0.009765625 TEBIBYTE, PER MONTH PER ACCOUNT #
# 40.00 USD PER TEBIBYTE, FOR 0.009765625 TEBIBYTE AND ABOVE, PER MONTH PER ACCOUNT  #
#                                       GLOBAL                                       #
#                             SNAPSHOTS MESSAGE BACKLOG                              #
#                                   EAF4-71D0-17E0                                   #
#                            0.27 USD PER GIBIBYTE MONTH                             #
#                                       GLOBAL                                       #
#                    SUBSCRIPTIONS RETAINED ACKNOWLEDGED MESSAGES                    #
#                                   3C0B-A83B-E6EE                                   #
#                            0.27 USD PER GIBIBYTE MONTH                             #
#                                       GLOBAL                                       #
######################################################################################

#*************************************************************************************
# *              1/2 X 605 GIB X 7 DAYS = 2118 GIB-DAYS OF STORAGE USED,              *
# * FOR WHICH THE CHARGE IS 2118 GIB-DAYS X (1/30 MONTHS/DAY) X $0.27/GIB-MONTH = $19 *
# *                                    IN A 30-DAY                                    *
# *************************************************************************************/

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

@app.route("/pricing/datastore")
def datastore_pricing():
    data={}
    
    d = task_pricing()
    m_count = d['data']['daily_tasks'] *  30

    data['reads']= (d['data']['daily_tasks'] - globals['datastore']['read-quota']) * 30 
    data['writes']= (d['data']['daily_tasks'] - globals['datastore']['write-quota']) * 30 
    data['deletes']= (d['data']['daily_tasks'] - globals['datastore']['delete-quota']) * 30 
    data['stored_kb']= (( d['data']['daily_tasks'] * \
        d['data']['task_size_kb'] ) - globals['datastore']['storage-quota'] ) *  3/4.0
    
    data['stored_gb']=data['stored_kb'] / 1024 / 1024.0

    data['DataStore reads'] = data['reads']/100000 * globals['datastore']['reads'] 
    data['DataStore writes'] = data['writes']/100000 * globals['datastore']['writes']
    data['DataStore deletes'] = data['deletes']/100000  * globals['datastore']['deletes']
    data['DataStore storage'] = data['stored_gb'] * globals['datastore']['storage']
    data['Datastore fees'] = data['DataStore reads'] + data['DataStore writes'] + \
                             data['DataStore deletes'] + data['DataStore storage']

    output = { 'data': data, 'globals': globals}
    return output
    

@app.route('/pricing/estimate/<id>')
def get_static(id=None):
    base_url='https://cloud.google.com/products/calculator/#id='
    get_url=base_url+id
    print(get_url)

    # headers = {
    # 'Access-Control-Allow-Origin': '*',
    # 'Access-Control-Allow-Methods': 'GET',gcloud iam service-accounts keys create  --iam-account my-iam-account@somedomain.com key.json
    # 'Access-Control-Allow-Headers': 'Content-Type',
    # 'Access-Control-Max-Age': '3600',
    # 'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:52.0) Gecko/20100101 Firefox/52.0'
    # }
    req = requests.get(get_url)
    soup = BeautifulSoup(req.content, 'html.parser')
    return soup.prettify()
    #soup.
    #return ""


@app.route('/pricing/bigtable_storage/<dtype>/<size>/<unit>')
def bigtable_storage_pricing(dtype=None, size=0, unit=None):
    
    data = {}
    messages = {}
    bt_price = {'SSD':0.17, 'HDD':0.26}
    data['type'] = dtype
    if dtype not in bt_price.keys():
        dtype='SSD'
        messages['default_type'] ='Unrecognized Storage Type: Using SSD'
    
    data['size'] = size
    
    data['unit']=unit
    if unit.upper() not in units.keys():
        unit='GB'
        messages['default_unit'] = 'Unrecognized Unit Type: Using GB'

    data['fees'] = bt_price[dtype] * size * units[unit]
    output= {'globals':globals,'messages': messages, 'data': data}
    return output

@app.route("/pricing/ds_pricing/")
def __def_ds_pricing():
    return ds_pricing()

def get_input(reads=30000, writes=20000, storage=100, scale=0.1):
    inputs = {}
    inputs['reads']   = reads #30000
    inputs['writes']  = writes #20000
    inputs['storage'] = storage #100 #* (10**12)  #100 TB
    inputs['scale']   = scale #globals['scaling']
    return inputs

def scale_data(data,inputs):
    data['scaler'] = 1 + inputs['scale']
    data['reads'] = inputs['reads'] * data['scaler']
    data['writes'] = inputs['writes'] * data['scaler']
    data['storage']  = inputs['storage'] * data['scaler']
    return data



@app.route("/pricing/ds/<int:reads>/<int:writes>/<int:storage>/<float:scale>")
def ds_pricing(reads=30000, writes=20000, storage=100, scale=0.1):

    data={}
    inputs = get_input(reads,writes,storage,scale)
    data=scale_data(data,inputs)

    data['location'] = 'nam5'
    data['storage_base_cost'] = .18
    data['storage_cost'] = round(data['storage_base_cost'] * data['storage'] * 10**3,2) # TB to GB

    data['read_base_cost'] = .06
    data['write_base_cost'] = .18
    data['delete_base_cost'] = .02

    data['io_unit'] = 100000.0
    data['monthly_reads'] = data['reads'] * globals['seconds_to_month']
    data['monthly_writes'] = data['writes'] * globals['seconds_to_month']

    data['read_cost'] = round(data['monthly_reads'] / data['io_unit'] * data['read_base_cost'],2)
    data['write_cost'] = round(data['monthly_writes']  / data['io_unit'] * data['write_base_cost'],2)
    data['io_cost'] = round(data['read_cost'] + data['write_cost'],2)
    data['total_cost'] = round(data['io_cost'] + data['storage_cost'],2)
    
    {key: '${:,.2f}'.format(value) for key, value in data.items() if 'cost' in key}
    output= {'inputs': inputs, 'globals': globals,'data': data}
    return output    


@app.route("/pricing/leanplum/json", methods=['GET','OPTIONS'])
def leanplum_json():
    o1 = ds_pricing()['data']
    o2 = bt_pricing()['data']
    o3 = spanner_pricing()['data']
    output = { 'globals' :globals , 'datastore': o1, 'bigtable': o2, 'spanner' :o3} 
    return output 

@app.route("/pricing/leanplum/json/<int:reads>/<int:writes>/<int:storage>/<float:scale>", methods=['GET','OPTIONS'])
def leanplum_json_params(reads=30000, writes=20000, storage=100, scale=0.1):
    o1 = ds_pricing(reads,writes,storage,scale)['data']
    o2 = bt_pricing(reads,writes,storage,scale)['data']
    o3 = spanner_pricing(reads,writes,storage,scale)['data']
    output = { 'Datastore': o1, 'Bigtable': o2, 'Spanner' :o3} 
    return output


@app.route("/pricing/leanplum/html")
def leanplum_html():
    o1 = json2html.convert(ds_pricing()['data'])
    o2 = json2html.convert(bt_pricing()['data'])
    o3 = json2html.convert(spanner_pricing()['data'])
    gh =json2html.convert(globals)
    #output = { 'globals' :globals , 'datastore': o1, 'bigtable': o2, 'spanner' :o3} 
    #html = json2html.convert(output)
    return o1 + o2 + o3


@app.route("/pricing/leanplum/<int:reads>/<int:writes>/<int:storage>/<float:scale>")
def leanplum_pricing(reads=30000, writes=20000, storage=100, scale=0.1):
    o1 = json2html.convert(ds_pricing(reads,writes,storage,scale)['data'])
    o2 = json2html.convert(bt_pricing(reads,writes,storage,scale)['data'])
    o3 = json2html.convert(spanner_pricing(reads,writes,storage,scale)['data'])
    return o1 + o2 + o3
    #gh =json2html.convert(globals)


@app.route("/pricing/bt_nodes/")
def __def_bt_pricing():
    return bt_pricing()

@app.route("/pricing/bt/<int:reads>/<int:writes>/<int:storage>/<float:scale>")
def bt_pricing(reads=30000, writes=20000, storage=100, scale=0.1):
     
    data={}
    inputs = get_input(reads,writes,storage,scale)
    data=scale_data(data,inputs)
    

    #multi region - 10K R/s, 10 W/s
    data['read_nodes_min']  = math.ceil(data['reads'] / 10000.0)
    data['write_nodes_min'] = math.ceil(data['writes'] / 10000.0)
    data['storage_nodes_min'] = math.ceil(data['storage'] / 2.5)

    data['nodes'] = int(max(data['read_nodes_min'],data['write_nodes_min'],data['storage_nodes_min']))
    data['nodes_read_capacity'] = data['nodes'] * 10000
    data['nodes_write_capacity'] = data['nodes'] * 10000

    data['location'] = 'us-central1'
    data['storage_base_cost'] = 0.17
    data['storage_cost'] = round(data['storage_base_cost'] * data['storage'] * 10**3,2) # TB to GB

    data['node_base_cost'] = 0.65
    data['node_cost'] = round(data['node_base_cost'] * data['nodes'] * 24 * 30,2)

    data['total_cost_single_region'] = round(data['storage_cost']  + data['node_cost'],2)

    data['replication_cost'] = round(data['writes'] / 1024 * 0.11,2)
    data['total_cost'] = data['total_cost_single_region'] * 2 + data['replication_cost']

    {key: '${:,.2f}'.format(value) for key, value in data.items() if 'cost' in key}
    output= {'inputs': inputs, 'globals':globals,'data': data}
    return output    

@app.route("/pricing/tasks")
def task_pricing():
    data={}
    data['tasks_per_second']=10000
    data['task_size_kb']=1.0

    data['daily_tasks'] = data['tasks_per_second'] * globals['seconds_to_days']
    data['monthly_tasks'] = data['daily_tasks'] * 30

    # no negatives
    data['billable_tasks'] = max( data['monthly_tasks'] - (5 * 10*10 ), 0)
    data['task_fees'] = data['billable_tasks']/(10**7) * globals['task_rates']
    
    output= {'globals':globals,'data': data}
    return output

@app.route("/pricing/spanner/")
def __def_spanner_pricing():
    return spanner_pricing()

@app.route("/pricing/spanner/<int:reads>/<int:writes>/<int:storage>/<float:scale>")
def spanner_pricing(reads=30000, writes=20000, storage=100, scale=0.1):

    data={}
    inputs = get_input(reads,writes,storage,scale)
    data=scale_data(data,inputs)
    
    data['read_nodes_min']  = math.ceil(data['reads'] / 7000.0)
    data['write_nodes_min'] = math.ceil(data['writes']   /1800.0)
    data['storage_nodes_min'] = math.ceil(data['storage'] / 2.0)
    

    data['nodes'] = int(max(data['read_nodes_min'],data['write_nodes_min'],data['storage_nodes_min'])) 
    data['nodes_read_capacity'] = '{:,} / sec'.format(data['nodes'] * 7000)
    data['nodes_write_capacity'] = '{:,} / sec'.format(data['nodes'] * 1800)
   
    #cost = {k: v for k, v in data.items() if 'cost' in k}
    app.logger.info('test')
    #data['CostNode'] = sorted(cost, key=cost.get, reverse=True)[:3]

    data['location'] = 'nam3'
    data['storage_base_cost'] = 0.50
    data['storage_cost'] = data['storage_base_cost'] * data['storage'] * 10**3 # TB to GB

    data['node_base_cost'] = 3.0
    data['node_cost'] = data['node_base_cost'] * data['nodes'] * 24 * 30
    data['total_cost'] =  data['storage_cost']  + data['node_cost']

    
    {key: '${:,.2f}'.format(value) for key, value in data.items() if 'cost' in key}

    output= {'globals':globals,'data': data}
    return output

@app.route("/pricing/pubsub")
def pubsub_pricing():
    data={}
    #3 MiB/second x 3600 seconds/hour x 24 hours/day x 30 days/month x 1 month/(2^20 MiB/TiB) = 7.416 TiB
   
    data['messages_per_second']=370000
    data['avg_msg_size_kb']=1.0#kb
    data['average_subscription_count']=100
    data['per_second_throughput'] = data['messages_per_second'] * data['avg_msg_size_kb'] * (data['average_subscription_count']+1)
    data['gbs'] = data['per_second_throughput']  /1024/1024
    data['daily-gb'] = data['gbs'] * globals['seconds_to_days']
    data['monthly-gb'] = data['daily-gb'] * 30
    data['monthly-tb'] = data['monthly-gb']/1024.0
    data['monthly_charged_tbs'] = data['monthly-tb'] - globals['free'] #TBs
    data['core-fees'] = data['monthly_charged_tbs'] * globals['core_fee']
   

    #subscriptions
   
    #data['average_subscription_count']=5
    data['retention_active']=1
    data['retention_active_percent']=.05

    data['subscription_retention_term_volume'] = data['daily-gb'] * globals['retention_term']
    data['subscription_fees'] = data['subscription_retention_term_volume'] \
                                 * globals['subscription_retention_fee'] \
                                 * data['retention_active'] * data['retention_active_percent']
    
    #snapshots
    data['snapshot_active']=0
    data['snapshots_per_month']=1
    data['avg_snapshot_size'] = data['daily-gb'] * 1/2
    data['snapshot_fees'] = 1/2 * data['snapshots_per_month'] \
                            * data['average_subscription_count'] \
                            * data['daily-gb'] \
                            * data['avg_msg_size_kb'] \
                            * globals['snapshot_fee'] * data['snapshot_active']

    data['total_fees'] = "{0:.2f}".format(data['snapshot_fees'] + data ['subscription_fees'] \
        + data['core-fees'])

    output= {'globals':globals,'data': data}
    return output #jsonify(output) #globals,data #jsonify(data)
    #dstr=json.dumps(data, indent=4)

    #return "<pre>Fees are {0}</pre>".format(dstr) 

@app.route('/app/')
def webapp():
    return render_template('public/index.html')

@app.route('/')
def index():
    return site_map()

# https://stackoverflow.com/questions/13317536/get-list-of-all-routes-defined-in-the-flask-app
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
    link_text='<br><a href="{0}"> {1}</a>'
    op=" "
    for t in links:
        print(t)
        op = op + link_text.format(t[0],t[1])
    return op

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80)