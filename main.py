import hmac
import json
import optparse
import uuid
from datetime import datetime
from hashlib import sha256
from time import mktime

import requests


class private_api:

    def __init__(self, host, organisation_id, key, secret, verbose=False):
        self.key = key
        self.secret = secret
        self.organisation_id = organisation_id
        self.host = host
        self.verbose = verbose

    def request(self, method, path, query, body):

        xtime = self.get_epoch_ms_from_now()
        xnonce = str(uuid.uuid4())

        message = bytearray(self.key, 'utf-8')
        message += bytearray('\x00', 'utf-8')
        message += bytearray(str(xtime), 'utf-8')
        message += bytearray('\x00', 'utf-8')
        message += bytearray(xnonce, 'utf-8')
        message += bytearray('\x00', 'utf-8')
        message += bytearray('\x00', 'utf-8')
        message += bytearray(self.organisation_id, 'utf-8')
        message += bytearray('\x00', 'utf-8')
        message += bytearray('\x00', 'utf-8')
        message += bytearray(method, 'utf-8')
        message += bytearray('\x00', 'utf-8')
        message += bytearray(path, 'utf-8')
        message += bytearray('\x00', 'utf-8')
        message += bytearray(query, 'utf-8')

        if body:
            body_json = json.dumps(body)
            message += bytearray('\x00', 'utf-8')
            message += bytearray(body_json, 'utf-8')

        digest = hmac.new(bytearray(self.secret, 'utf-8'), message, sha256).hexdigest()
        xauth = self.key + ":" + digest

        headers = {
            'X-Time': str(xtime),
            'X-Nonce': xnonce,
            'X-Auth': xauth,
            'Content-Type': 'application/json',
            'X-Organization-Id': self.organisation_id,
            'X-Request-Id': str(uuid.uuid4())
        }

        s = requests.Session()
        s.headers = headers

        url = self.host + path
        if query:
            url += '?' + query

        if self.verbose:
            print(method, url)

        if body:
            response = s.request(method, url, data=body_json)
        else:
            response = s.request(method, url)

        if response.status_code == 200:
            return response.json()
        elif response.content:
            raise Exception(str(response.status_code) + ": " + response.reason + ": " + str(response.content))
        else:
            raise Exception(str(response.status_code) + ": " + response.reason)

    def get_epoch_ms_from_now(self):
        now = datetime.now()
        now_ec_since_epoch = mktime(now.timetuple()) + now.microsecond / 1000000.0
        return int(now_ec_since_epoch * 1000)

    def algo_settings_from_response(self, algorithm, algo_response):
        algo_setting = None
        for item in algo_response['miningAlgorithms']:
            if item['algorithm'] == algorithm:
                algo_setting = item

        if algo_setting is None:
            raise Exception('Settings for algorithm not found in algo_response parameter')

        return algo_setting

    def get_rig_status(self, rig_id):
        return self.request('GET', f'/main/api/v2/mining/rig2/{rig_id}', '', None)

    def update_rig_status(self, rig_id, action):
        req_body = {'rigId': rig_id, 'action': action}
        return self.request('POST', '/main/api/v2/mining/rigs/status2', '', req_body)


def activate_rig(api, rig_id):
    print(f'Activating rig:{rig_id}')
    rig_status = api.get_rig_status(rig_id)
    mining = False
    if rig_status:
        if rig_status['minerStatus'] == 'MINING':
            mining = True

    if not mining:
        resp = api.update_rig_status(rig_id, 'START')
        print(f'Response from activate: {resp}')
    else:
        print('Already MINING!')


def deactivate_rig(api, rig_id):
    print(f'Deactivating rig:{rig_id}')
    rig_status = api.get_rig_status(rig_id)
    mining = True
    if rig_status:
        if rig_status['minerStatus'] == 'STOPPED':
            mining = False

    if mining:
        resp = api.update_rig_status(rig_id, 'STOP')
        print(f'Response from deactivate: {resp}')
    else:
        print('Already STOPPED!')


if __name__ == "__main__":
    parser = optparse.OptionParser()

    parser.add_option('-b', '--base_url', dest="base", help="Api base url", default="https://api2.nicehash.com")
    parser.add_option('-o', '--organization_id', dest="org", help="Organization id")
    parser.add_option('-k', '--key', dest="key", help="Api key")
    parser.add_option('-s', '--secret', dest="secret", help="Secret for api key")
    parser.add_option('-r', '--rig', dest="rigId", help="Rig ID to activate or deactivate")
    parser.add_option('-a', '--activate', action="store_true", dest="activate", help="Activate rig")
    parser.add_option('-d', '--deactivate', action="store_true", dest="deactivate", help="Deactivate rig")

    options, args = parser.parse_args()
    private_api = private_api(options.base, options.org, options.key, options.secret)

    try:
        if options.activate:
            activate_rig(private_api, options.rigId)
        elif options.deactivate:
            deactivate_rig(private_api, options.rigId)
    except Exception as ex:
        print("Unexpected error:", ex)
        exit(1)

    exit(0)
