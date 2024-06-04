from requests import Request, Session
from urllib.parse import urljoin, urlparse, urlunparse
from time import time
import urllib3,logging,json
urllib3.disable_warnings()

_session = Session()
logging.basicConfig(level=logging.INFO,format='%(message)s')

class Client:
    def __init__(self, host='', timeout=10, insecure=False, access_token=None, client_id=None, client_secret=None, username=None, password=None):
        self.host = host
        self.timeout = timeout
        self.insecure = insecure
        self.token_type = 'Bearer'
        self.access_token = access_token
        self.access_token_expires = None
        self.client_id = client_id
        self.client_secret = client_secret        

    def cppm(self, method, uri, query_params=None, body=None, authz=True):
        headers = {}
        if authz:
            headers['Authorization'] = self.authHeader()
        url = self.getUrl(uri)        
        try: 
            response = _session.request(method, url, params=query_params,
            headers=headers, json=body, timeout=self.timeout, verify=not self.insecure)
            return response.json()
        except Exception as e:
            print(e)
            return None
                
    def getUrl(self, url):
        rel = urlparse(url)
        path = rel.path
        if len(path):
            if path[0] != '/':
                path = '/' + path
            if path[0:4] != '/api':
                path = '/api' + path
        return urljoin('https://' + self.host, urlunparse((rel.scheme, rel.netloc, path, rel.params, rel.query, rel.fragment)))

    def authHeader(self):
        if not self.access_token:
            data = {'grant_type': 'client_credentials', 'client_id': self.client_id, 'client_secret': self.client_secret}            
            oauth = self.cppm('POST', '/oauth', None, data, False)            
            try:
                self.token_type = oauth['token_type']
                self.access_token = oauth['access_token']
                self.access_token_expires = time() + oauth['expires_in']
                return (self.token_type + ' ' + self.access_token)
            except Exception as e:
                logging.info(f"Connection to ClearPass failed: {e}")
        return (self.token_type + ' ' + self.access_token)

def main(secret,table):
    if secret=='' or table=='0':
        print('Enter secret and your table number')
        return
    endpoint=False
    print('Starting connection to ClearPass!')
    cp = Client(host='10.254.1.23',insecure=True,client_secret=secret,client_id=f'Client{table}')
    result=cp.cppm(uri='api/endpoint',method='GET')    
    if result:
        for i in result['_embedded']['items']:
            if i['mac_address']==f'0200000000{table}':
                endpoint=True
                if 'secure' in i['attributes'].keys():
                    if i['attributes']['secure']=='true':
                        print(f"Endpoint {i['mac_address']} is secure")
                    elif i['attributes']['secure']=='false':
                        print(f"Endpoint {i['mac_address']} is not secure")
                else:
                    print(f"Endpoint {i['mac_address']} exists")
        if not endpoint:
            print('Endpoint does not exist. Adding Endpoint.')
            data={"mac_address": f"0200000000{table}","status": "Unknown", "attributes": {"secure": "false"}}
            result=cp.cppm(method='POST',uri='api/endpoint',body=data)
            print('Endpoint added')
            

if __name__ == '__main__':
        main('','0')
