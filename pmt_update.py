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

# TODO: Update a pmt, ensure no overwrite

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

def update_payment(**data):
  acct = data['fb_acct']
  headers = { 'Content-Type': 'application/xml' }
  # Check if payment exists
  xmlreq_chk = """<?xml version="1.0" encoding="utf-8"?>
                <request method="payment.list">
                  <payment>
                    <invoice_id>""" + data['invid'] + """</invoice_id>
                  </payment>
                </request>"""
  resp_chk = requests.get(
    url=config[f'{acct}']['API_URL'],
    auth=HTTPBasicAuth(config[f'{acct}']['AUTH_TOKEN'], 'X'),
    data=xmlreq_chk,
    headers=headers
  )

  if resp_chk.status_code == 200:
    if resp_chk.text.split('total="')[1][0] == '0':
      return f"A payment for invoice #{data['invnmbr']} already exists, cannot overwrite"
    else:
    # Update payment
      xmlreq_up = """<?xml version="1.0" encoding="utf-8"?>
                    <request method="payment.create">
                      <payment>
                        <invoice_id>""" + data['invid'] + """</invoice_id>
                        <date>""" + data['pmt_date'] + """</date>
                        <amount>""" + data['amt'] + """</amount>
                        <type>""" + data['pmt_type'] + """</type>          
                        <notes>Updated via script</notes>
                      </payment>
                    </request>"""

      resp_up = requests.get(
        url=config[f'{acct}']['API_URL'],
        auth=HTTPBasicAuth(config[f'{acct}']['AUTH_TOKEN'], 'X'),
        data=xmlreq_up,
        headers=headers
      )

      if resp_up.status_code == 200:
        return f"Inv #{data['invid']} updated"
      else:
        return f"Could not update payment info for inv #{data['invid']}"
  else:
    return f"Could not update payment info for inv #{data['invid']}"

for f in os.listdir(PATH):
  df = pd.read_csv(PATH + f)
  wantedcols = ['YY', 'MM', 'DD', 'Dep #', 'Payee or comment', 'FundTy', 'TYPE', 'GL-$-Amt']
  apidf = df[wantedcols].copy()
  apijson = json.loads(apidf.to_json(orient='index'))

  invoices = []
  status_log = []
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
      'pmt_date': '20' + str(data['YY']) + '-' + str(data['MM']).zfill(2) + '-' + str(data['DD']).zfill(2),
      'invnmbr': invnmbr,
      'invid': get_invoiceID(invnmbr, fb_acct),
      'fb_acct': fb_acct,
      'amt': str(data['GL-$-Amt']),
      'pmt_type': 'Check' if data['FundTy'] == 'chq' else 'Bank Transfer',
    }

    invoices.append(invjson)
  
  # pprint.pprint(invoices)

  # Create payments for each invoice
  for i in invoices:
    status_log.append(update_payment(**i))
  
  # print(status_log)