## To update payments in batches

import os
import yaml
import json
import requests
import pandas as pd
import numpy as np
import xml.etree.ElementTree as ET

import pprint

import asyncio

from requests.auth import HTTPBasicAuth

config = yaml.load(open('config.yml'))

PATH = './uploaded_csvs/'

def get_invoiceID(number, fb_acct):
  invoiceID = []
  xml_req = """<!--?xml version="1.0" encoding="utf-8"?-->
                <request method="invoice.list">
                  <number>""" + number + """</number>
                </request>"""
  headers = { 'Content-Type': 'application/xml' }

  resp = requests.get(
    url=config[f'{fb_acct}']['API_URL'],
    auth=HTTPBasicAuth(config[f'{fb_acct}']['AUTH_TOKEN'], 'X'),
    data=xml_req,
    headers=headers
  )

  root = ET.fromstring(resp.content)
  for child in root.iter('{http://www.freshbooks.com/api/}invoice_id'):
    invoiceID.append(child.text)

  if len(invoiceID) != 1:
    return f'Error: Cannot find invoice #{number} from account {fb_acct}'
  else:
    return invoiceID[0]

def update_payment(invoiceID, amt, pmt_type, notes):
  xml_req = """<?xml version="1.0" encoding="utf-8"?>
                <request method="payment.create">
                  <payment>
                    <invoice_id>""" + invoiceID + """</invoice_id>
                    <amount>""" + amt + """</amount>
                    <currency_code>CAD</currency_code>
                    <type>""" + pmt_type + """</type>               
                    <notes>""" + notes + """ added via script</notes>
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

for f in os.listdir(PATH):
  df = pd.read_csv(PATH + f)
  wantedcols = ['YY', 'MM', 'DD', 'Dep #', 'Payee or comment', 'FundTy', 'TYPE', 'GL-$-Amt']
  apidf = df[wantedcols].copy()
  apijson = json.loads(apidf.to_json(orient='index'))

  invoices = []

  # Parse the invoice numbers from data entry
  for data in apijson.values():
    inv_entry = data['Payee or comment']
    inv_split = inv_entry.split('#')
    fb_acct = data['TYPE']

    if inv_entry.count('#') > 1:
      invnmbr = (f'{inv_split[1]}-#{inv_split[2]}').strip()
    else:
      invnmbr = (inv_entry.split('#'))[1][0:7].strip()

    invjson = {
      'invnmbr': invnmbr,
      'invid': get_invoiceID(invnmbr, fb_acct),
      'fbacct': fb_acct
    }

    invoices.append(invjson)
