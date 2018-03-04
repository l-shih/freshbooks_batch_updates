## To update payments in batches

## TODO: read a csv file to update invoices
## TODO: allow multiple freshbooks accounts

import yaml
import requests
import xml.etree.ElementTree as ET

from requests.auth import HTTPBasicAuth

config = yaml.load(open('config.yml'))
api_url = config['CLBC']['API_URL']
token = config['CLBC']['AUTH_TOKEN']

def get_invoiceID(number):
  invoiceID = []
  xml_req = """<!--?xml version="1.0" encoding="utf-8"?-->
                <request method="invoice.list">
                  <number>""" + number + """</number>
                </request>"""
  headers = { 'Content-Type': 'application/xml' }

  resp = requests.get(
    url=api_url,
    auth=HTTPBasicAuth(token, 'X'),
    data=xml_req,
    headers=headers
  )

  root = ET.fromstring(resp.content)
  for child in root.iter('{http://www.freshbooks.com/api/}invoice_id'):
    invoiceID.append(child.text)

  if len(invoiceID) != 1:
    return f'Error: Check your invoice number'
  else:
    return invoiceID

def update_payment(invoiceID, amt, pmt_type, notes):
  xml_req = """<?xml version="1.0" encoding="utf-8"?>
                    <request method="payment.create">
                      <payment>
                        <invoice_id>""" + invoiceID + """</invoice_id>
                        <amount>""" + amt + """</amount>
                        <currency_code>CAD</currency_code>
                        <type>""" + pmt_type + """</type>               
                        <notes>""" + notes + """</notes>
                      </payment>
                    </request>"""
  headers = { 'Content-Type': 'application/xml' }
  
  resp = requests.get(
    url=api_url,
    auth=HTTPBasicAuth(token, 'X'),
    data=xml_req,
    headers=headers
  )

  return resp.text



