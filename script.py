import argparse
import logging
import os
import re
import subprocess
from collections import namedtuple

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


def chunks(a_list, n):
  """Yield successive n-sized chunks from l."""
  for i in range(0, len(a_list), n):
    yield i,i + n


def open_connection(session_handle, query):
  vendor_url = 'https://www.costcotravel.com/carSearch.act'
  data = {
    'cs': 1,
    'fromHomePage': False,
    'fromCarVendorMainMenu': True,
  }

  data.update(query)

  result = session_handle.post(vendor_url, data=data)
  assert result.status_code == 200
  return parse_vendors(result.content), result

Vendor = namedtuple('Vendor', ['brand', 'agency_code', 'address'])

def parse_vendors(content):
  html = BeautifulSoup(content)
  table = html.select('#carAgencyTitleDiv > table')
  rows = table[0].contents

  vendors = []
  for row in rows:
    if row.find_all('td'):
      address = row.find_all('td')[0].text
      vendor, agency_code = row.find_all('input')[0]['id'].split('_')
      vendors.append(Vendor(brand=vendor, agency_code=agency_code, address=address))
  return vendors


def get_quotes(vendors, previous_result, query, page=None):
  """
  Minimal working curl command:
  curl https://www.costcotravel.com/carAgencySelection.act
  -H 'Cookie: JSESSIONID=6561E0532492F11DD5F2881F2BA4569A;  BIGipServerpool-prod-app=!r6rO13w4p8V3beLCd3dqWKLWYEL+b3e8+YyrGcQg9X6zCc78ikyUBYXow/+lnST9jM3jXrkQE12x7w=='
  -H 'X-CSRF-Token: 194e2f0fd52c27e0f462b44eb18af1f6876af023355a718f4ab191efa48aebd213b3b8eefd4c0963f2dc75149feac10c87df6b564c12c485533e1f7c164155e9'
  --data 'carAgenciesForVendors=[{'vendorId': 'BG', 'agencyCodes': ['SFOC08']}, {'vendorId': 'AV', 'agencyCodes': ['SFOC02']}]&pickupDate=01/21/2017&cas=3&pickupTime=12:00 PM&dropoffDate=01/22/2017&dropoffTime=12:00 PM&carSearchInModifyFlow=False'

  :param vendors:
  :return:
  """

  can = re.split(r',|;', previous_result.headers['Set-Cookie'])

  cookie = '; '.join(filter(lambda x: not any(y.lower() in x.lower() for y in ['HttpOnly', 'Path', 'Secure']), can))
  csrf_token = previous_result.headers['csrf-token']
  quote_url = 'https://www.costcotravel.com/carAgencySelection.act'
  header = {
    'Cookie': cookie,
    'X-CSRF-Token': csrf_token,
  }

  all_prices = []
  winning_chunk = (-1, -1)

  for start, end in chunks(vendors, 4):
    vendor_chunk = vendors[start:end]
    locs = {}
    for vendor, agency, address in vendor_chunk:
      if vendor in locs:
        locs[str(vendor)].append(str(agency))
      else:
        locs[str(vendor)] = [str(agency)]

    carAgenciesForVendors = []

    for vendor, agencies in locs.items():
      carAgenciesForVendors.append({'vendorId': vendor, 'agencyCodes': agencies})

    data = {
      'cas': 3,
      'carAgenciesForVendors': carAgenciesForVendors,
    }
    data.update(query)
    logger.debug(header)
    logger.debug(data)

    cmds = ['curl', quote_url]
    for k, v in header.items():
      cmds.append("-H '{}: {}'".format(k, v))
    cmds.append('--data')


    if not page:
      serialized_data = []
      for k, v in data.items():
        serialized_data.append("{}={}".format(k, v))

      cmds.append("'{}'".format('&'.join(serialized_data)))

      final_cmd = ' '.join(cmds)
      logger.debug(final_cmd)
      with open(os.devnull, 'w') as devnull:
        output = subprocess.check_output(final_cmd, shell=True, stderr=devnull, stdin=devnull)

      assert 'Econ' in output
      quotes_html = BeautifulSoup(output)

      chunk_prices = [float(div.text.strip('$')) for div in quotes_html.find_all('div', {'class': 'carCell'})]
      if not all_prices or min(chunk_prices) <= min(all_prices):
        winning_chunk = (start, end)

      all_prices.extend(chunk_prices)

    else:
      quote_query_data = {
        'cas': 5,
        'distanceSelected': False,
        'selectedPage': page
      }

      serialized_data = []
      for k, v in quote_query_data.items():
        serialized_data.append("{}={}".format(k, v))

      cmds.append("'{}'".format('&'.join(serialized_data)))

      final_cmd = ' '.join(cmds)
      logger.debug(final_cmd)
      with open(os.devnull, 'w') as devnull:
        output = subprocess.check_output(final_cmd, shell=True, stderr=devnull, stdin=devnull)

      vendors = parse_vendors(output)
      return vendors

  return all_prices, winning_chunk


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Process some integers.')
  parser.add_argument('--debug', dest='debug', action='store_true')
  args = parser.parse_args()
  if args.debug:
    logger.setLevel(logging.DEBUG)
  else:
    logger.setLevel(logging.INFO)

  with requests.Session() as session:
    query = {
      'pickupCityLocationTypeSearch': 1,
      'pickupCountry': 'US',
      'pickupCity': 'SAN FRANCISCO-CA',
      'pickupAsAirport': False,
      'pickupZip': '',
      'pickupCityRadius': 25,

      'dropoffCityLocationTypeSearch': 1,
      'dropoffCountry': 'US',
      'dropoffCity': 'SAN FRANCISCO-CA',
      'dropoffAsAirport': False,
      'dropoffZip': '',
      'dropoffStreetAddress': '',
      'dropoffCityRadius': 25,

      'driverAge': 25,

      "pickupDate": "01/28/2017",
      "pickupTime": "09:00 AM",
      "dropoffDate": "01/30/2017",
      "dropoffTime": "09:00 AM",

      'carSearchInModifyFlow': False,

    }
    vendors, result = open_connection(session, query)
    for page in range(1, 5):
      vendors = get_quotes(vendors, result, query, page)
      quotes, winning_chunk = get_quotes(vendors, result, query)
      print "page {}: {} at {}".format(page, sorted(quotes)[:20], winning_chunk)
