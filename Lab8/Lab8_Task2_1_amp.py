import requests,urllib3,logging
urllib3.disable_warnings()
import xml.etree.ElementTree as ET


class amp():

    def __init__(self,username,host,password):
        self.user=username
        self.host=host
        self.password=password
        self.headers={'Content-Type':'application/x-www-form-urlencoded','Cache-Control':'no-cache'}
        self.credentials=f'credential_0={self.user}&credential_1={self.password}&destination=/&login=Log In'
        self.ampsession = requests.Session()

    def login(self):
        try:
            response = self.ampsession.post(f'https://{self.host}:443/LOGIN', headers=self.headers, data=self.credentials, verify=False, timeout=2)
            return response
        except:
            print(f'Failed login to {self.host}')

    def get(self,command):
        try:
            response = self.ampsession.get(f'https://{self.host}:443/{command}.xml', headers=self.headers, verify=False, timeout=2)
            return response
        except:
            print(f'Failed get {command} from {self.host}')


if __name__ == '__main__':

    amp1 = amp('admin','10.254.1.113','admin')
    amp1.login()
    res=amp1.get('ap_list')
    if res:
        print(res.content.decode('utf-8'))
        try:
            tree=ET.fromstring(res.content.decode('utf-8'))
            for i in tree.iter('ap'):
                devgroup=i.find('group').text
                devname=i.find('name').text
                devip=i.find('lan_ip').text
                devup=i.find('is_up').text
                devcat=i.find('device_category').text
                print(f'##### Parsing result\nDevice IP: {devip}\nDevice name: {devname}\nDevise is UP: {devup}\nCategory: {devcat}')
        except:
            print('Filed to parse')
    else:
        print('No data received from AMP server')
