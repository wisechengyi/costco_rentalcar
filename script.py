import logging
import re
import subprocess

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


def chunks(a_list, n):
  """Yield successive n-sized chunks from l."""
  for i in range(0, len(a_list), n):
    yield a_list[i:i + n]


def get_vendors(session_handle, query):
  vendor_url = 'https://www.costcotravel.com/carSearch.act'
  data = {
    'cs': 1,
    'fromHomePage': False,
    'fromCarVendorMainMenu': True,
  }

  data.update(query)

  result = session_handle.post(vendor_url, data=data)
  assert result.status_code == 200
  html = BeautifulSoup(result.content)
  table = html.select('#carAgencyTitleDiv > table')

  vendors = []

  for row in table[0].contents:
    if row.find_all('td'):
      address = row.find_all('td')[0].text
      vendor, agency_code = row.find_all('input')[0]['id'].split('_')
      vendors.append((vendor, agency_code, address))

  return vendors, result


def get_quotes(vendors, previous_result, query):
  """
  Minimal working curl command:
  curl https://www.costcotravel.com/carAgencySelection.act
  -H 'Cookie: JSESSIONID=6561E0532492F11DD5F2881F2BA4569A;  BIGipServerpool-prod-app=!r6rO13w4p8V3beLCd3dqWKLWYEL+b3e8+YyrGcQg9X6zCc78ikyUBYXow/+lnST9jM3jXrkQE12x7w=='
  -H 'X-CSRF-Token: 194e2f0fd52c27e0f462b44eb18af1f6876af023355a718f4ab191efa48aebd213b3b8eefd4c0963f2dc75149feac10c87df6b564c12c485533e1f7c164155e9'
  --data 'carAgenciesForVendors=[{'vendorId': 'BG', 'agencyCodes': ['SFOC08']}, {'vendorId': 'AV', 'agencyCodes': ['SFOC02']}]&pickupDate=01/21/2017&cas=3&pickupTime=12:00 PM&dropoffDate=01/22/2017&dropoffTime=12:00 PM&carSearchInModifyFlow=False'

  :param vendors:
  :param server_csrf_token:
  :return:
  """

  can = re.split(r',|;', previous_result.headers['Set-Cookie'])

  cookie = '; '.join(filter(lambda x: not any(y.lower() in x.lower() for y in ['HttpOnly', 'Path', 'Secure']), can))
  csrf_token = previous_result.headers['csrf-token']

  # logger.debug(cookie)
  quote_url = 'https://www.costcotravel.com/carAgencySelection.act'
  header = {
    'Cookie': cookie,
    'X-CSRF-Token': csrf_token,
  }

  all_prices = []
  for vendor_chunk in chunks(vendors, 4):
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

    ed = []
    for k, v in data.items():
      ed.append("{}={}".format(k, v))

    cmds.append("'{}'".format('&'.join(ed)))
    final_cmd = ' '.join(cmds)
    logger.debug(final_cmd)

    output = subprocess.check_output(final_cmd, shell=True)
    assert 'Econ' in output
    quotes_html = BeautifulSoup(output)

    for div in quotes_html.find_all('div', {'class': 'carCell'}):
      all_prices.append(float(div.text.strip('$')))

  return all_prices


if __name__ == '__main__':
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

      "pickupDate": "01/21/2017",
      "pickupTime": "12:00 PM",
      "dropoffDate": "01/22/2017",
      "dropoffTime": "12:00 PM",

      'carSearchInModifyFlow': False,

    }

    vendors, result = get_vendors(session, query)
    quotes = get_quotes(vendors, result, query)
    print sorted(quotes)
