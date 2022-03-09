#!/usr/bin/env python3
#from import __init__ as mod
import json
import requests
from requests.exceptions import HTTPError

base_url='https://cloudbilling.googleapis.com/v1/services'
api_key='AIzaSyDtBYBBr9Dd8qK65xU6V0Ls3VmDRM8GOXA'
get_url='{}?key={}'.format(base_url,api_key)

filter = ['Compute Engine']


#https://cloud.google.com/billing/docs/reference/rest/v1/services.skus/list#pricingexpression

def fetch(url):
    #print(url)
    response = requests.get(url)
    response.raise_for_status()
    json_response = response.json()
    return json_response

def dive(e):
    sku_url='{}/{}/skus?key={}'.format(base_url,e['serviceId'],api_key)
    #print(sku_url)
    response = requests.get(sku_url)
    response.raise_for_status()
    json_response = response.json()
    #print(json_response)
    
    #{ print('\t{},{},{}'.format(e['skuId'], e['description'], e['category']['serviceDisplayName'])) for e in json_response['skus'] }
    #print(json_response)
    #print(len(json_response['skus']))
    print(json_response['skus'])
    return ''


# try:
def fetch_service_list():
    json_response = fetch(get_url)
    { print(dive(e)) for e in json_response['services']  } #if any(f in e['displayName'] for f in filter) }

def main():
    fetch_service_list()

if __name__=='__main__':
    main()
    #print(mod)





# except HTTPError as http_err:
#     print(f'HTTP error occurred: {http_err}')
# except Exception as err:
#     print(f'Other error occurred: {err}')