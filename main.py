import optparse
import os
from flask import Flask
from private_api import PrivateApi
from google.cloud import secretmanager

def activate_rig(api, rig_id):
    print(f'Activating rig:{rig_id}')
    rig_status = api.get_rig_status(rig_id)
    mining = False
    if rig_status:
        if rig_status['minerStatus'] == 'MINING':
            mining = True

    resp = {}
    if not mining:
        resp = api.update_rig_status(rig_id, 'START')
        print(f'Response from activate: {resp}')
    else:
        print('Already MINING!')

    return resp


def deactivate_rig(api, rig_id):
    print(f'Deactivating rig:{rig_id}')
    rig_status = api.get_rig_status(rig_id)
    mining = True
    if rig_status:
        if rig_status['minerStatus'] == 'STOPPED':
            mining = False

    resp = {}
    if mining:
        resp = api.update_rig_status(rig_id, 'STOP')
        print(f'Response from deactivate: {resp}')
    else:
        print('Already STOPPED!')

    return resp


app = Flask(__name__)
PROJECT_ID = os.environ.get("PROJECTID")
secrets = secretmanager.SecretManagerServiceClient()
ORG = secrets.access_secret_version(request={"name": "projects/"+PROJECT_ID+"/secrets/NICEHASH_ORG/versions/1"}).payload.data.decode("utf-8")
KEY = secrets.access_secret_version(request={"name": "projects/"+PROJECT_ID+"/secrets/NICEHASH_KEY/versions/1"}).payload.data.decode("utf-8")
SECRET = secrets.access_secret_version(request={"name": "projects/"+PROJECT_ID+"/secrets/NICEHASH_SECRET/versions/1"}).payload.data.decode("utf-8")

@app.route("/", methods=['GET'])
def hello_world():
    return 'hello world!'


@app.route("/activate/<rig_id>", methods=['PUT'])
def activate(rig_id):
    base = os.environ.get('BASE_URL', 'https://api2.nicehash.com')
    org = ORG
    key = KEY
    secret = SECRET
    api = PrivateApi(base, org, key, secret)

    resp = {}
    try:
        resp = activate_rig(api, rig_id)
    except Exception as ex:
        print("Unexpected error:", ex)

    return resp


@app.route("/deactivate/<rig_id>", methods=['PUT'])
def deactivate(rig_id):
    base = os.environ.get('BASE_URL', 'https://api2.nicehash.com')
    org = ORG
    key = KEY
    secret = SECRET
    api = PrivateApi(base, org, key, secret)

    resp = {}
    try:
        resp = deactivate_rig(api, rig_id)
    except Exception as ex:
        print("Unexpected error:", ex)

    return resp

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
