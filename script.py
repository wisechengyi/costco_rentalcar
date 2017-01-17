import email.utils as eut
import logging
import re
import urllib
from datetime import datetime

import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger()


def get_vendors(session_handle):
  vendor_url = 'https://www.costcotravel.com/carSearch.act'
  data = {
    'cs': 1,
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

    'pickupDate': '01/21/2017',
    'dropoffDate': '01/22/2017',
    'pickupTime': '12:00 PM',
    'dropoffTime': '12:00 PM',
    'driverAge': 25,

    'fromHomePage': False,
    'fromCarVendorMainMenu': True,
    'carSearchInModifyFlow': False,
    # 'uid': '1484528899909_653.6177851957367',

  }

  result = session_handle.post(vendor_url, data=data)
  assert result.status_code == 200
  csrf_token = result.headers['csrf-token']
  html = BeautifulSoup(result.content)
  table = html.select('#carAgencyTitleDiv > table')

  vendors = []

  for row in table[0].contents:
    if row.find_all('td'):
      address = row.find_all('td')[0].text
      vendor, agency_code = row.find_all('input')[0]['id'].split('_')
      vendors.append((vendor, agency_code, address))

  return vendors, result


def get_quotes(vendors, session_handle, previous_result):
  """
  curl 'https://www.costcotravel.com/carAgencySelection.act' -H 'Host: www.costcotravel.com'
  -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10.11; rv:50.0) Gecko/20100101 Firefox/50.0'
  -H 'Accept: */*'
  -H 'Accept-Language: en-US,en;q=0.5'
  -H 'X-CSRF-Token: <client generated token>'
  -H 'Content-Type: application/x-www-form-urlencoded;charset=UTF-8'
  -H 'Referer: https://www.costcotravel.com/h=3001'
  -H 'Cookie: JSESSIONID=619831155848BCA2EDE3BF49C47FCDDA;
    BIGipServerpool-prod-app=!KCkILZ0AQdXppdjCd3dqWKLWYEL+bxnuFLCzWjhuULZ9niQsFy+j0hfyUUc5DeftahUftmr9u+GOJA==;
    _ga=GA1.2.509779762.1484527852; Csrf-token=de9edd7187345e24e05b3603d629d0b3233060fd567eb2af27a4bd5a229d7d7ad9560505e230a1518008dcbabce4300b7326759d04c1636605853c42f8ddfb74;
    SESSION_TIMESTAMP=1484539968110; _gat=1;
    RENTAL_CAR_SEARCH_WIDGET_VALUES={"pickUpLocation":{"type":"city","code":"SAN FRANCISCO-CA","name":"SAN FRANCISCO, CA, US","cityCode":"SAN FRANCISCO","stateCode":"","countryCode":"US","latitude":"","longitude":""},"pickUpDate":"01/21/2017","pickUpTime":"12:00 PM","dropOffLocation":{"type":"city","code":"SAN FRANCISCO-CA","name":"SAN FRANCISCO, CA, US","cityCode":"SAN FRANCISCO","stateCode":"","countryCode":"US","latitude":"","longitude":""},"dropOffDate":"01/22/2017","dropOffTime":"12:00 PM","driverAge":25}'
  --data 'cas=3&carAgenciesForVendors=[{"vendorId":"ET","agencyCodes":["E123GP"]},{"vendorId":"AL","agencyCodes":["SFOC78"]}]&carSearchInModifyFlow=false&pickupDate=01/21/2017&pickupTime=12:00 PM&dropoffDate=01/22/2017&dropoffTime=12:00 PM&uid=1484540447270_850.4426179924067'

  :param vendors:
  :param server_csrf_token:
  :return:
  """

  can = re.split(r',|;', previous_result.headers['Set-Cookie'])
  # for x in ['Secure;', 'HttpOnly,', 'HttpOnly;', 'Path=/;']:
  #   cookie = cookie.replace(x, '')
  # filtered_things = []
  # for x in can:
  #   if not any(x.lower() in y.lower() for y in ['HttpOnly', 'Path', 'Secure']):
  #     filtered_things.append(x)

  cookie = '; '.join(filter(lambda x: not any(y.lower() in x.lower() for y in ['HttpOnly', 'Path', 'Secure']), can))

  t = datetime(*eut.parsedate(previous_result.headers['Date'])[:6])

  csrf_token = previous_result.headers['csrf-token']

  # logger.debug(cookie)
  quote_url = 'https://www.costcotravel.com/carAgencySelection.act'
  header = {
    'Cookie': cookie,
    'X-CSRF-Token': csrf_token,
  }
  data = {
    'cas': 3,
    'carAgenciesForVendors': [
      {
        'vendorId': 'ET',
        'agencyCodes': ["E123GP"]
      },
      {
        'vendorId': 'AV',
        'agencyCodes': ["SFOC01"]
      }
    ],
    'carSearchInModifyFlow': False,
    "pickupDate": "01/21/2017",
    "pickupTime": "12:00 PM",
    "dropoffDate": "01/22/2017",
    "dropoffTime": "12:00 PM",
    # "uid": "1484554729812_780.7547816966148",
  }

  # session_handle.headers.update(header)
  # final_header = session_handle.headers
  logger.debug(header)
  logger.debug(data)



  # http = urllib3.PoolManager()
  # r = session_handle.request('GET', quote_url,
  #                  headers=header,
  #                  body='cas=3&carAgenciesForVendors=[{"vendorId":"ET","agencyCodes":["E12347"]},{"vendorId":"BG","agencyCodes":["SFOC08"]}]&carSearchInModifyFlow=false&pickupDate=01/21/2017&pickupTime=12:00 PM&dropoffDate=01/22/2017&dropoffTime=12:00 PM')
  # x = r.read()
  #
  # cmd = """\
  # curl 'https://www.costcotravel.com/carAgencySelection.act' -H 'Cookie: JSESSIONID=166156FD6196F2045DC7EFF1E9191FA7; BIGipServerpool-prod-app=!87b8TUntT+0/R0PCd3dqWKLWYEL+b0MyFiFUi1xPdGyNYGJPo4KvZpSB4oVGTcHfXUiEa3ztI6hOog=='  -H 'X-CSRF-Token: 5c0b850401e8c9d6512412fc9cb05a949aedd26cc3c30d38c8b7e49e1df10065090be2255b90dd8a176d1244ffe68c4b99210820fead55cd1261f102caa19a6e' --data 'cas=3&carAgenciesForVendors=[{"vendorId":"ET","agencyCodes":["E12347"]},{"vendorId":"BG","agencyCodes":["SFOC08"]}]&carSearchInModifyFlow=false&pickupDate=01/21/2017&pickupTime=12:00 PM&dropoffDate=01/22/2017&dropoffTime=12:00 PM'
  # """
  # output = subprocess.check_output(cmd, shell=True)

  result = requests.post(
    url=quote_url,
    headers=header,
    data='cas=3&carAgenciesForVendors=[{"vendorId":"ET","agencyCodes":["E12347"]},{"vendorId":"BG","agencyCodes":["SFOC08"]}]&carSearchInModifyFlow=false&pickupDate=01/21/2017&pickupTime=12:00 PM&dropoffDate=01/22/2017&dropoffTime=12:00 PM'
  )

  cmds = ['curl', quote_url]
  for k, v in header.items():
    cmds.append("-H '{}: {}'".format(k, v))
  cmds.append('--data')


  ed = []
  for k, v in data.items():
    ed.append("{}={}".format(k,v ))

  cmds.append("'{}'".format('&'.join(ed)))


  print(' '.join(cmds))

  assert result.status_code == 200
  assert 'Econ' in result.content


if __name__ == '__main__':
  with requests.Session() as session:
    vendors, result = get_vendors(session)
    # with open('text.html', 'w') as f:
    #   f.write(result.content)
    # logger.info(vendors)
    get_quotes(vendors, session, result)
