from pycentral.base import ArubaCentralBase
from pycentral.monitoring import Sites
from pycentral.configuration import Groups, Devices, ApConfiguration, Wlan
import json, time, urllib3, requests

def createGroup(cent,group_name):
    #Create new groups
    print(f'### Attempting to create new group {group_name}:')
    Group = {
     "group": group_name,
     "group_attributes": {
      "template_info": {"Wired": False,"Wireless": False},
      "group_properties": {"AllowedDevTypes": ["AccessPoints"],
      "Architecture": "AOS10",
      "ApNetworkRole": "Standard"      
     }}}
    try:
        resp = cent.command(apiMethod="POST",apiPath="/configuration/v3/groups",
           apiData=Group,apiParams={"limit": 20, "offset": 0})
        if resp['code'] == 400:
            print(f"[{resp['msg']['description']}]")
        elif resp['code'] == 201:
            print(f"[Success]")
        else:
            print(f'[Failure]')
    except Exception as e:
        print(f'Failed to create new group {new_group}: {e}')

def createSite(cent,site_name):
    #Create and list sites    
    try:
        print(f'### Attempting to create new site {site_name}:')
        centSites = Sites()
        addr = {'address':'1234 FranklinRd','city':'Southfield','country':'US'}
        resp = centSites.create_site(cent,site_name,addr)        
        if resp['code'] == 200:
            print(f'[Success]')
        elif resp['code'] == 400:
            print(f'[Site {site_name} already exists]')
        else:
            print(f'[Failure]')
    except Exception as e:
        print(f'Failed to create new site {site_name}: {e}')

def getAPs(cent):
    #Request a list of APs and save MACs, serials
    try:
        serials=[]
        print(f'### Collecting information about APs from Central:')
        aps = cent.command(apiMethod="GET",apiPath="/monitoring/v2/aps")
        if aps['code']==200:
            print('[Success]')
            print(f"Number of APs connected: {aps['msg']['count']}")
            for i in aps['msg']['aps']:
                print(f"AP model: {i['model']}, AP status: {i['status']}, AP IP addr: {i['ip_address']}")
                serials.extend([i['serial']])
            print(f'Collected APs serial numbers: {serials}')
        else:
            print('[Failure]')
    except Exception as e:
        print(f'Failued to get a list of APs from Central: {e}')
    return serials

def moveAPs(cent,serials,group_name):
    #Move APs to a group
    try:
        print(f'### Attempting to move APs to group {group_name}:')
        centDevices = Devices()
        resp = centDevices.move_devices(cent,group_name,serials)        
        if resp['code'] == 200:
            print('[Success]')
        else:
            print(f'[Failure]')
    except Exception as e:
        print(f'Failed to move APs to group {group_name}: {e}')

def assignSite(cent,serials,site_name):
    #Assign APs to the site
    try:
        print(f'### Attempting to associate APs with site {site_name}:')
        centSites = Sites()        
        resp = centSites.get_sites(cent)
        for i in resp['msg']['sites']:
            if i['site_details']['name']=='Southfield':
                site_id=i['site_id']        
        resp = centSites.associate_devices(cent,site_id,'IAP',serials)        
        if resp['code'] == 200:
            print(f'[Success]')
        else:
            print(f'[Failure]')
    except Exception as e:
        print(f'Failed to associate APs with site: {e}')

def apConfig(cent,group_name):
    #Select the region and add auth server
    try:        
        centAPConf = ApConfiguration()
        data={"groups": ["ap-test"],"country": "US"}
        print('### Configuring the country code:')
        resp = cent.command(apiMethod="PUT",apiPath=f'/configuration/v1/country',apiData=data)
        if resp['code']==201:
            print('[Success]')
        else:
            print('[Failure]')
        print('### Collecting configuration from APs:')
        resp = centAPConf.get_ap_config(cent,group_name)        
        cli=resp['msg']
        cli.extend(["wlan auth-server cppm","  ip 10.254.1.23","  key Aruba123!","  port 1812", "  acctport 1813"])
        clis = {"clis": cli}
        if resp['code']==200:
            print('[Success]')
        else:
            print('[Failure]')
        print('### Pushing Auth server configuration to APs:')
        resp = centAPConf.replace_ap(cent,group_name,clis)
        if resp['code']==200:
            print('[Success]')
        else:
            print('[Failure]')
    except Exception as e:
        print(f'Failed to configure APs: {e}')

def createWlan(cent,group_name,wlan_name,table):
    #Create new WLAN
    try:      
        centWlan = Wlan()
        with open('wlan.json') as file:
            wlan_data = file.read().replace('<table>',f'{table}')
        print(f'### Creating new WLAN {wlan_name}:')
        resp = centWlan.create_full_wlan(cent, group_name, wlan_name, json.loads(wlan_data))
        if resp['code']==200:
            print('[Success]')
        elif resp['code']==400:
            print(f"[{resp['msg']['description']}]")
        else:
            print('[Failure]')        
    except Exception as e:
        print(f'Failed to create WLAN: {e}')

def createLabel(cent,label_name):
    #Create new Label
    try:
        print(f'### Creating new label {label_name}:')
        new_label = {"category_id": 1,"label_name": label_name}
        resp = cent.command("POST","/central/v1/labels",new_label)
        if resp['code']==200:
            print('[Success]')
        elif resp['code']==400:
            print(f"[{resp['msg']['description']}]")
        else:
            print('[Failure]')
    except Exception as e:
        print(f'Failed to create the label: {e}')

def assignLabel(cent,serials,label_name):
    #Assign label to APs
    try:
        print(f'### Assigning label {label_name} to APs {serials}')
        resp=cent.command("GET","/central/v1/labels")
        for i in resp['msg']['labels']:
            if i['label_name']==label_name:
                label_id=i['label_id']
        labels = {
        "device_type": "IAP",
        "label_id": label_id,
        "device_ids": serials
        }
        resp=cent.command("POST","/central/v2/labels/associations",labels)
        if resp['code']==200:
            print('[Success]')
        else:
            print('[Failure]')
    except Exception as e:
        print(f'Failed to assign the label: {e}')

def wait(timeout):
    print(f'Timeout for {timeout} seconds...')
    time.sleep(timeout)


def configAcc1(table):
    #Configure Access1 switch: create VLAN X0, allow new VLAN on int 11,12 and 24
    try:
        print("### Connecting to Acc1 switch")
        url=f'https://10.251.{table}.103:443/rest/v10.10/'
        creds={'username': 'admin', 'password': 'aruba123'}
        s=requests.Session()
        s.post(url + 'login', params=creds, verify=False, timeout=3)
        print("[Success]")
        print("### Pushing switch Acc1's configuration:")        
        data={"name":f"VLAN{table}0","id":table*10}        
        s.post(url + 'system/vlans', data=json.dumps(data), verify=False, timeout=3)                
        data={"vlan_mode": "native-untagged", "vlan_tag": {f"{table}5": f"/rest/v10.10/system/vlans/{table}5"},
              "vlan_trunks": {f"{table}0": f"/rest/v10.10/system/vlans/{table}0",f"{table}5": f"/rest/v10.10/system/vlans/{table}5"}}
        resp=s.put(url + 'system/interfaces/1%2F1%2F11', data=json.dumps(data), verify=False, timeout=3)
        data={"vlan_mode": "native-untagged", "vlan_tag": {f"{table}6": f"/rest/v10.10/system/vlans/{table}6"},
              "vlan_trunks": {f"{table}0": f"/rest/v10.10/system/vlans/{table}0",f"{table}6": f"/rest/v10.10/system/vlans/{table}6"}}
        resp=s.put(url + 'system/interfaces/1%2F1%2F12', data=json.dumps(data), verify=False, timeout=3)
        data={"vlan_mode": "native-untagged", "vlan_trunks": {f"{table}0": f"/rest/v10.10/system/vlans/{table}0",
            f"{table}5": f"/rest/v10.10/system/vlans/{table}5",f"{table}6": f"/rest/v10.10/system/vlans/{table}6",
            f"{table}9": f"/rest/v10.10/system/vlans/{table}9"}}
        resp=s.put(url + 'system/interfaces/1%2F1%2F24', data=json.dumps(data), verify=False, timeout=3)       
        print("[Success]")
        s.post(url + 'logout', verify=False, timeout=5)
    except Exception as e:
        print("[Failure]")
        print(f"Failied to configure Acc1 switch :{e}")

def configCore2(table):
    #Configure switch Core2: create VLAN X0, SVI X0 and allow new VLAN on int 1/1/1.
    try:
        print("### Connecting to Core2 switch")
        url=f'https://10.251.{table}.102:443/rest/v10.04/'
        creds={'username': 'admin', 'password': 'aruba123'}
        s=requests.Session()
        login=s.post(url + 'login', params=creds, verify=False, timeout=3)        
        print("[Success]")        
        print("### Pushing switch Core2's configuration:")
        data={"name":f"VLAN{table}0","id":table*10}        
        s.post(url + 'system/vlans', data=json.dumps(data), verify=False, timeout=3)
        data={"admin": "up","user_config": {"admin": "up"}, "routing": False, "vlan_mode": "native-untagged",
            "vlan_trunks": {f"{table}0": f"/rest/v10.04/system/vlans/{table}0",
            f"{table}5": f"/rest/v10.04/system/vlans/{table}5",f"{table}6": f"/rest/v10.04/system/vlans/{table}6",
            f"{table}9": f"/rest/v10.04/system/vlans/{table}9"}}
        resp=s.put(url + 'system/interfaces/1%2F1%2F1', data=json.dumps(data), verify=False, timeout=3)
        data={"name": f"vlan{table}0", "ip4_address": f"10.1.{table}0.1/24","type": "vlan"}
        resp=s.post(url + f'system/interfaces', data=json.dumps(data), verify=False, timeout=3)                
        data={"ipv4_ucast_server": ["10.254.1.21"],"port": {f"vlan{table}0": f"/rest/v10.04/system/interfaces/vlan{table}0"},
         "vrf": {"default": "/rest/v10.04/system/vrfs/default"}}
        resp=s.post(url + f'system/dhcp_relays', data=json.dumps(data), verify=False, timeout=3)        
        print("[Success]")
        #print(resp.content) #troubleshooting
        s.post(url + 'logout', verify=False, timeout=5)
    except Exception as e:
        print("[Failure]")
        print(f"Failied to configure Core2 switch :{e}")        

def main(token,table):
    #Define objects, execute functions
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    if token=='' or table==0:
        print('Add your access token and table number')
        return
    central_info={'base_url':'https://apigw-uswest4.central.arubanetworks.com',"token":{"access_token": token}}
    print('### Accessing HPE Aruba Central')
    cent = ArubaCentralBase(central_info)
    print('[Success]')
    aps = getAPs(cent)
    createSite(cent,'Southfield')
    createGroup(cent,'ap-test')
    moveAPs(cent,aps,'ap-test')
    wait(15)
    assignSite(cent,aps,'Southfield')
    apConfig(cent,'ap-test')
    createWlan(cent,'ap-test',f'p57-t{table}-corp',table)
    createLabel(cent,'AOS10-APs')
    assignLabel(cent,aps,'AOS10-APs')
    configAcc1(table)
    configCore2(table)


if __name__ == '__main__':
    main('',0)
