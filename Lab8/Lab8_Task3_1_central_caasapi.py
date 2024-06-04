from pycentral.base import ArubaCentralBase

def list_aps(cent):
    try:
        aps=cent.command(apiMethod="GET",apiPath="/monitoring/v2/aps")
        print(f'### Connection to Aruba Central is successful')
        return aps
    except:
        print(f'### Failed to get a list of devices')

def caas_post(cent,gw_mac,gw_group):
    #Push configuration to GW
    with open('gw.txt') as file:
        gw_cli_cmds = file.read().splitlines()
    gw = {'cli_cmds': gw_cli_cmds}
    base_resp=cent.command(apiMethod="POST",apiPath="/caasapi/v1/exec/cmd",apiData=gw,apiParams={"limit": 20, "offset": 0, "group_name": f"{gw_group}/{gw_mac}", "cid": cent.central_info['customer_id']})
    if '_global_result' in base_resp['msg']:
        print('Config pushed to GW successful')
    else:
        print('Config pushed to GW failed')

def caas_get(cent,gw_mac,gw_group):
    command = 'caasapi/v1/showcommand/object/effective'
    apiParams = {"limit": 20, "offset": 0, "group_name": f"{gw_group}/{gw_mac}"}
    result = cent.command(apiMethod="GET",apiPath=f"/{command}",apiParams=apiParams)
    return result

def main():
    gw_mac='<GW_MAC_address>'
    gw_group='<GW_Group_in_Central>'
    central_info={     
         'base_url':'https://apigw-uswest4.central.arubanetworks.com',     
         "token": {
          "access_token": '<access_token>'}}   
    cent = ArubaCentralBase(central_info)    
    aps=list_aps(cent)    
    if aps!=None:
        for i in aps['msg']['aps']:
            print(f"AP with IP {i['ip_address']} is connected")
    else:
        print('No APs are connected to Central')
    if gw_mac!='':
        gw1=caas_get(cent,gw_mac,gw_group)        
        if gw1!=None:
            for i in gw1['msg']['config']:
                if 'hostname' in i or i.startswith("vlan"):
                    print(i)
            if 'hostname gw1 ' not in gw1['msg']['config']:
                print('Pushing configs to GW')
                caas_post(cent,gw_mac,gw_group)
            else:
                print('GW configured with hostname "gw1"')
    

if __name__ == "__main__":
    main()
    
