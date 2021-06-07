# Import Section
from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from sqlalchemy_utils import database_exists
from datetime import datetime
import requests
import json
from dotenv import load_dotenv
import os
import time

# load all environment variables
load_dotenv()
DB_PATH = os.getenv("DB_PATH")
MERAKI_BASE_URL = os.getenv("MERAKI_BASE_URL")
MERAKI_API_KEY = os.getenv("MERAKI_API_KEY")
ORG_NAME = os.getenv("ORG_NAME")

# global variables
headers = dict()
headers['X-Cisco-Meraki-API-Key'] = MERAKI_API_KEY
headers['Content-Type'] = "application/json"
headers['Accept'] = "application/json"
base_url = MERAKI_BASE_URL

#Global variables
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#DB Models
class Franchisee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    store_number = db.Column(db.String(10), unique=True, nullable=False)
    store_name = db.Column(db.String(50), unique=False, nullable=False)
    order_number = db.Column(db.String(20), unique=True, nullable=False)
    organzation_id = db.Column(db.String(20), unique=False, nullable=True)
    organzation_name = db.Column(db.String(20), unique=False, nullable=True)
    network_id = db.Column(db.String(20), unique=False, nullable=True)
    template_name = db.Column(db.String(20), unique=False, nullable=True)
    is_processed = db.Column(db.Boolean, nullable=False)
    submit_date = db.Column(db.DateTime, nullable=False)
    process_date = db.Column(db.DateTime, nullable=True)

#Initialize DB
if not database_exists(DB_PATH):
    db.create_all()


#Methods
#Returns location and time of accessing device
def getSystemTimeAndLocation():
    #request user ip
    userIPRequest = requests.get('https://get.geojs.io/v1/ip.json')
    userIP = userIPRequest.json()['ip']

    #request geo information based on ip
    geoRequestURL = 'https://get.geojs.io/v1/ip/geo/' + userIP + '.json'
    geoRequest = requests.get(geoRequestURL)
    geoData = geoRequest.json()

    #create info string
    location = geoData['country']
    timezone = geoData['timezone']
    current_time=datetime.now().strftime("%d %b %Y, %I:%M %p")
    timeAndLocation = "System Information: {}, {} (Timezone: {})".format(location, current_time, timezone)

    return timeAndLocation

#Generic API call function
def meraki_api(method, uri, payload=None):
    response = requests.request(method, base_url+uri, headers=headers, data=json.dumps(payload))
    return response


##Routes
@app.route('/')
def get_start():
    try:
        #Page without error message and defined header links
        return render_template('start.html', timeAndLocation=getSystemTimeAndLocation())
    except Exception as e:
        print(e)
        #OR the following to show error message
        return render_template('start.html', error=True, errormessage=f"Error: {e}", timeAndLocation=getSystemTimeAndLocation())


@app.route('/corporate/register')
def get_corporate_register():
    try:
        # get all organizations
        orgs = meraki_api('GET', '/organizations')
        if orgs.status_code == 200:
            orgs = json.loads(orgs.text)
            orgs_id_name = dict()
            orgs_templates = dict()
            for org in orgs:
                orgs_id_name[org['id']] = org['name']
        else:
            return render_template('corporate_register.html', error=True, errormessage=f"Error: {json.loads(orgs.text)['errors']}", errorcode=orgs.status_code, timeAndLocation=getSystemTimeAndLocation())

        # get all unprocessed franchisees
        franchisees = Franchisee.query.filter_by(is_processed=False).all()

        return render_template('corporate_register.html', orgs=orgs_id_name, franchisees=franchisees, timeAndLocation=getSystemTimeAndLocation())
#        return render_template('corporate_register.html', orgs=orgs_id_name, franchisees=franchisees, devices=devices_by_order, timeAndLocation=getSystemTimeAndLocation())
    except Exception as e:
        print(e)
        #OR the following to show error message
        return render_template('corporate_register.html', error=True, errormessage=f"Error: {e}", timeAndLocation=getSystemTimeAndLocation())


@app.route('/corporate/register/confirm_org', methods=['POST'])
def post_corporate_confirm_org():
    try:
        data = json.loads(request.form['data'])
        store_number = data['store_number']
        store_name = data['store_name']
        order_number = data['order_number']
        org_id = data['org_id']
        org_name = data['org_name']

        # claim into org
        payload = {
            "orders": [order_number]
        }
        claim_into_org = meraki_api('POST', f'/organizations/{org_id}/claim', payload)
        if claim_into_org.status_code == 200:
            claim_into_org = json.loads(claim_into_org.text)
            if claim_into_org['orders'] == []:
                return f"Error: Invalid order number"
        else:
            return f"Error: {json.loads(claim_into_org.text)['errors']}"

        # create a new network for the franchisee
        payload = {
            "name": store_name,
            "timeZone": "Asia/Shanghai",
            "productTypes": [
                "appliance",
                "switch",
                "wireless"
            ]
        }
        new_network = meraki_api('POST', f'/organizations/{org_id}/networks', payload)
        if new_network.status_code == 201:
            new_network = json.loads(new_network.text)
            new_network_id = new_network['id']
            print(new_network)
        else:
            return f"Error: {json.loads(new_network.text)['errors']}"

        # get serials of the order
        devices = meraki_api('GET', f'/organizations/{org_id}/inventoryDevices?usedState=unused')
        if devices.status_code == 200:
            devices = json.loads(devices.text)
            serials = []
            grouped_devices = dict()
            grouped_devices['models'] = dict()
            grouped_devices['count'] = 0
            for device in devices:
                if device['orderNumber'] == order_number:
                    serials.append(device['serial'])
                    if device['model'] not in grouped_devices['models']:
                        grouped_devices['models'][device['model']] = []
                    grouped_devices['models'][device['model']].append(device['serial'])
                    grouped_devices['count'] += 1

        # claim devices into the network
        payload = {
            "serials": serials
        }
        new_network_ready = False
        while not new_network_ready:
            claim_into_network = meraki_api('POST', f'/networks/{new_network_id}/devices/claim', payload)
            if claim_into_network.status_code == 200:
                new_network_ready = True

        franchisee = Franchisee.query.filter_by(store_number=store_number).first()
        franchisee.organzation_id = org_id
        franchisee.organzation_name = org_name
        franchisee.network_id = new_network_id
        db.session.commit()

        # get config templates
        config_templates = meraki_api('GET', f'/organizations/{org_id}/configTemplates')
        if config_templates.status_code == 200:
            config_templates = json.loads(config_templates.text)
            for config_template in config_templates:
                config_template.pop('productTypes')
                config_template.pop('timeZone')
        else:
            return f"Error: {json.loads(config_templates.text)['errors']}"

        return render_template('devices_template.html', devices=grouped_devices, config_templates=config_templates)
    except Exception as e:
        print(e)
        return f"Error: {e}"


@app.route('/corporate/register/confirm_template', methods=['POST'])
def post_corporate_confirm_template():
    try:
        data = json.loads(request.form['data'])
        store_number = data['store_number']
        template_id = data['template_id']
        template_name = data['template_name']

        # get store network ID
        franchisee = Franchisee.query.filter_by(store_number=store_number).first()
        network_id = franchisee.network_id

        # bind network to config template
        payload = {
            "configTemplateId": template_id,
            "autoBind": True
        }
        bind_network = meraki_api('POST', f'/networks/{network_id}/bind', payload)
        if bind_network.status_code != 200:
            return f"Error: {json.loads(bind_network.text)['errors']}"

        franchisee.is_processed = True
        franchisee.template_name = template_name
        franchisee.process_date = datetime.now()
        db.session.commit()

        return "Y"
    except Exception as e:
        print(e)
        return f"Error: {e}"


@app.route('/corporate/modify')
def get_corporate_modify():
    try:
        franchisees = Franchisee.query.all()

        #Page without error message and defined header links
        return render_template('corporate_modify.html', franchisees=franchisees, timeAndLocation=getSystemTimeAndLocation())
    except Exception as e:
        print(e)
        #OR the following to show error message
        return render_template('corporate_modify.html', error=True, errormessage=f"Error: {e}", timeAndLocation=getSystemTimeAndLocation())


@app.route('/corporate/modify', methods=['POST'])
def post_corporate_modify():
    try:
        data = json.loads(request.form['data'])
        old_store_number = data['old_store_number']
        old_store_name = data['old_store_name']
        new_store_number = data['new_store_number']
        new_store_name = data['new_store_name']
        number = False
        name = False

        if new_store_name != "":
            update_franchisee = Franchisee.query.filter_by(store_number=old_store_number).first()
            if update_franchisee.organzation_id:
                check_franchisee = Franchisee.query.filter_by(organzation_id=update_franchisee.organzation_id, store_name=update_franchisee.store_name)
                if check_franchisee.count() == 1:
                    # update network name
                    payload = {
                        "name": new_store_name
                    }
                    update_network = meraki_api('PUT', f'/networks/{update_franchisee.network_id}', payload)
                    if update_network.status_code == 200:
                        update_franchisee.store_name = new_store_name
                        db.session.commit()
                        name = True
            else:
                update_franchisee.store_name = new_store_name
                db.session.commit()
                name = True

        if new_store_number != "":
            check_franchisee = Franchisee.query.filter_by(store_number=new_store_number).first()
            if not check_franchisee:
                update_franchisee = Franchisee.query.filter_by(store_number=old_store_number).first()
                update_franchisee.store_number = new_store_number
                db.session.commit()
                number = True

        if number == True and name == True:
            return "Both"
        elif number == True and name == False:
            return "Number"
        elif number == False and name == True:
            return "Name"
        else:
            return "None"
    except Exception as e:
        print(f"{e}")
        return "None"


@app.route('/corporate/history')
def get_corporate_history():
    try:
        franchisees = Franchisee.query.all()

        #Page without error message and defined header links
        return render_template('corporate_history.html', franchisees=franchisees, timeAndLocation=getSystemTimeAndLocation())
    except Exception as e:
        print(e)
        #OR the following to show error message
        return render_template('corporate_history.html', error=True, errormessage=f"Error: {e}", timeAndLocation=getSystemTimeAndLocation())


@app.route('/franchisee')
def get_franchisee():
    try:
        #Page without error message and defined header links
        return render_template('franchisee.html', timeAndLocation=getSystemTimeAndLocation())
    except Exception as e:
        print(e)
        #OR the following to show error message
        return render_template('franchisee.html', error=True, errormessage=f"Error: {e}", timeAndLocation=getSystemTimeAndLocation())


@app.route('/franchisee', methods=['POST'])
def post_franchisee():
    try:
        # get input from franchisee
        store_name = request.form.get("store_name")
        order_number = request.form.get("order_number")

        # add to DB
        try:
            # assign with a temp store number
            if Franchisee.query.order_by('id').all():
                store_number = str(Franchisee.query.order_by('id').all()[-1].id + 1)
            else:
                store_number = "1"

            new_franchisee = Franchisee(store_number=store_number, store_name=store_name, order_number=order_number, is_processed=False, submit_date=datetime.now())
            db.session.add(new_franchisee)
            db.session.commit()
            return render_template('franchisee.html', success=True, successmessage=f"", timeAndLocation=getSystemTimeAndLocation())
        except exc.SQLAlchemyError as e:
            return render_template('franchisee.html', error=True, errormessage=f"Error: This record might exist in database already", timeAndLocation=getSystemTimeAndLocation())
    except Exception as e:
        print(e)
        return render_template('franchisee.html', error=True, errormessage=f"Error: {e}", timeAndLocation=getSystemTimeAndLocation())


#Main Function
if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=False)

