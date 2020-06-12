"""
This is doc string
"""
# sys
import sys
# config parser
import configparser
# working with json
import json
# subprocess
import subprocess
# working with requests
import requests
# urllib3
import urllib3

# config file
CURRENT_CONFIG_NAME = "sevpn.ini"
# get current script path and split by /
CURRENT_CONFIG = sys.argv[0].split('/')
# we got list. delete last item (script file name)
CURRENT_CONFIG.pop()
# add config file name
CURRENT_CONFIG.append(CURRENT_CONFIG_NAME)
# generate string: config file path
CURRENT_CONFIG = "/".join(CURRENT_CONFIG)
# init settings variable
SEVPN_SETTINGS = configparser.ConfigParser()
# try to read config file
try:
    SEVPN_SETTINGS.read(CURRENT_CONFIG)
except IOError:
    print('Cannot read: ' + CURRENT_CONFIG)
    exit()

# server url
SERVER_URL = SEVPN_SETTINGS["SERVER"]['URL'] + ":" + SEVPN_SETTINGS["SERVER"]['PORT']
# api url
API_URL = SERVER_URL + SEVPN_SETTINGS["SERVER"]["API"]
# adminhub
ADMIN_HUB = SEVPN_SETTINGS["SERVER"]["ADMIN_HUB"]
# server password
ADMIN_PASS = SEVPN_SETTINGS["SERVER"]["ADMIN_PASS"]
# headers for hub field
HUB_HEADERS = SEVPN_SETTINGS["HEADERS"]["HUBNAME"]
# headers for pass field
PASS_HEADERS = SEVPN_SETTINGS["HEADERS"]["PASSWORD"]
# my headers
HEADERS = {HUB_HEADERS: ADMIN_HUB, PASS_HEADERS: ADMIN_PASS}
# valid commands
VALID_COMMANDS = SEVPN_SETTINGS["SERVER"]["COMMANDS"].split(',')

# max ping count (1 try = 1 second, zabbix has 30 sec max timeout. Default: 3
# i choose 15 as maximum
PING_COUNT_MAX = int(SEVPN_SETTINGS["PING"]["MAX"])
# minimum ping tries
PING_COUNT_MIN = int(SEVPN_SETTINGS["PING"]["MAX"])
# default - average value
PING_COUNT_DEFAULT = int((PING_COUNT_MAX + PING_COUNT_MIN)/2)

def convert_bool(input_dict):
    """
    Get input dict. Replace Bool True/False to Int 1/0
    :param input_dict:
    :return:
    """
    output_dict = input_dict
    # select all keys and values
    for key, value in input_dict.items():
        # if value type is boolean
        if isinstance(value, type(True)):
            # convert to integer
            output_dict[key] = int(value)
    # return result dict
    return output_dict

def do_request(method, params):
    """
    This is doc string
    :param method:
    :param params:
    :return:
    """
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    fn_params = {"jsonrpc": "2.0", "id": "rpc_call_id", "method": ""}
    fn_params["method"] = method
    fn_params["params"] = params
    response = requests.post(API_URL, data=json.dumps(fn_params), headers=HEADERS, verify=False)
    return json.loads(response.text)

def bridge_discovery():
    """
    This is doc string
    :return:
    """
    fn_params = {}
    fn_method = "EnumLocalBridge"
    fn_result = do_request(fn_method, fn_params)
    zabbix_json = {"data": []}
    for cur_bridge in fn_result['result']['LocalBridgeList']:
        bridge_converted = convert_bool(cur_bridge)
        json_item = {}
        json_item["{#HUBNAME}"] = bridge_converted["HubNameLB_str"]
        json_item["{#IFNAME}"] = bridge_converted["DeviceName_str"]
        json_item["{#ACTIVE}"] = bridge_converted["Active_bool"]
        json_item["{#ONLINE}"] = bridge_converted["Online_bool"]
        json_item["{#TAPMODE}"] = bridge_converted["TapMode_bool"]
        zabbix_json["data"].append(json_item)
    return json.dumps(zabbix_json)


def bridge_support():
    """
    This is doc string
    :return:
    """
    fn_params = {}
    fn_method = "GetBridgeSupport"
    fn_result = do_request(fn_method, fn_params)
    fn_result['result'] = convert_bool(fn_result['result'])
    return json.dumps(fn_result)

def server_info():
    """
    This is doc string
    :return:
    """
    fn_params = {}
    fn_method = "GetServerInfo"
    fn_result = do_request(fn_method, fn_params)
    fn_result['result'] = convert_bool(fn_result['result'])
    return json.dumps(fn_result)

def server_status():
    """
    This is doc string
    :return:
    """
    fn_params = {}
    fn_method = "GetServerStatus"
    fn_result = do_request(fn_method, fn_params)
    fn_result['result'] = convert_bool(fn_result['result'])
    return json.dumps(fn_result)

def listener_discovery():
    """
    This is doc string
    :return:
    """
    fn_params = {}
    fn_method = "EnumListener"
    fn_result = do_request(fn_method, fn_params)
    zabbix_json = {"data": []}
    for cur_listener in fn_result['result']['ListenerList']:
        listener_converted = convert_bool(cur_listener)
        json_item = {}
        json_item["{#PORT}"] = listener_converted["Ports_u32"]
        json_item["{#ENABLED}"] = listener_converted["Enables_bool"]
        zabbix_json["data"].append(json_item)
    return json.dumps(zabbix_json)

def listener_stats():
    """
    This is doc string
    :return:
    """
    fn_params = {}
    fn_method = "EnumListener"
    fn_result = do_request(fn_method, fn_params)
    result_json = {}
    for cur_listener in fn_result['result']['ListenerList']:
        listener_converted = convert_bool(cur_listener)
        json_item = {}
        json_item["Errors_bool"] = listener_converted["Errors_bool"]
        json_item["Enables_bool"] = listener_converted["Enables_bool"]
        result_json[str(cur_listener["Ports_u32"])] = json_item
    return json.dumps(result_json)

def bridge_stats():
    """
    This is doc string
    :return:
    """
    fn_params = {}
    fn_method = "EnumLocalBridge"
    fn_result = do_request(fn_method, fn_params)
    result_json = {}
    for cur_item in fn_result['result']['LocalBridgeList']:
        item_converted = convert_bool(cur_item)
        json_item = {}
        json_item["Online_bool"] = item_converted["Online_bool"]
        json_item["Active_bool"] = item_converted["Active_bool"]
        cur_hub_name = item_converted["HubNameLB_str"]
        cur_dev_name = item_converted["DeviceName_str"]
        cur_tap_mode = item_converted["TapMode_bool"]
        if cur_hub_name not in result_json.keys():
            result_json[cur_hub_name] = {cur_dev_name: {str(cur_tap_mode): json_item}}
        elif cur_dev_name not in result_json[cur_hub_name].keys():
            result_json[cur_hub_name][cur_dev_name] = {str(cur_tap_mode): json_item}
        else:
            result_json[cur_hub_name][cur_dev_name][str(cur_tap_mode)] = json_item
    return json.dumps(result_json)

def hub_list():
    """
    This is doc string
    :return:
    """
    # get hub list
    fn_params = {}
    fn_method = "EnumHub"
    fn_result = do_request(fn_method, fn_params)
    return json.dumps(fn_result)

def hub_discovery():
    """
    This is doc string
    :return:
    """
    # get hub list
    fn_result = json.loads(hub_list())
    zabbix_json = {"data": []}
    for cur_item in fn_result['result']['HubList']:
        item_converted = convert_bool(cur_item)
        json_item = {}
        json_item["{#HUBNAME}"] = item_converted["HubName_str"]
        json_item["{#ONLINE}"] = item_converted["Online_bool"]
        json_item["{#TYPE}"] = item_converted["HubType_u32"]
        json_item["{#TRAFFICFILLED}"] = item_converted["IsTrafficFilled_bool"]
        zabbix_json["data"].append(json_item)
    return json.dumps(zabbix_json)

def get_hub_status(hub_name):
    """
    This is doc string
    :return:
    """
    # get hub
    fn_params = {"HubName_str": str(hub_name)}
    fn_method = "GetHubStatus"
    fn_result = do_request(fn_method, fn_params)
    return json.dumps(fn_result)

def hub_stats():
    """
    This is doc string
    :return:
    """
    result_json = {}
    # get hub list
    fn_hubs_dict = json.loads(hub_list())
    fn_hub_list = fn_hubs_dict['result']['HubList']
    for cur_item in fn_hub_list:
        cur_hub = json.loads(get_hub_status(cur_item["HubName_str"]))
        item_converted = convert_bool(cur_hub["result"])
        hub_name = item_converted["HubName_str"]
        json_item = {}
        for key, value in item_converted.items():
            json_item[key] = value
        result_json[hub_name] = json_item
    return json.dumps(result_json)

def cascade_list(hub_name):
    """
    This is doc string
    :return:
    """
    # get hub
    fn_params = {"HubName_str": str(hub_name)}
    fn_method = "EnumLink"
    fn_result = do_request(fn_method, fn_params)
    return json.dumps(fn_result)

def get_cascade_status(hub_name, cascade_name):
    """
    This is doc string
    :return:
    """
    # get hub
    fn_params = {"HubName_Ex_str": str(hub_name),
                 "AccountName_utf": cascade_name}
    fn_method = "GetLinkStatus"
    fn_result = do_request(fn_method, fn_params)
    return json.dumps(fn_result)

def cascade_discovery():
    """
    This is doc string
    :return:
    """
    zabbix_json = {"data": []}
    # get hubd list
    fn_hubs_dict = json.loads(hub_list())
    fn_hub_list = fn_hubs_dict['result']['HubList']
    for cur_hub_item in fn_hub_list:
        cur_hub_name = cur_hub_item["HubName_str"]
        cur_hub_cascades = json.loads(cascade_list(cur_hub_name))
        for cur_item in cur_hub_cascades["result"]["LinkList"]:
            json_item = {}
            item_converted = convert_bool(cur_item)
            cascade_name = item_converted["AccountName_utf"]
            json_item["{#HUBNAME}"] = cur_hub_name
            json_item["{#CASCADENAME}"] = cascade_name
            json_item["{#ONLINE}"] = item_converted["Online_bool"]
            json_item["{#CONNECTED}"] = item_converted["Connected_bool"]
            json_item["{#HOSTNAME}"] = item_converted["Hostname_str"]
            json_item["{#TARGETHUB}"] = item_converted["TargetHubName_str"]
            zabbix_json["data"].append(json_item)
    return json.dumps(zabbix_json)

def internal_ping_discovery():
    """this is docstring"""
    my_links = json.loads(cascade_discovery())
    new_links = []
    for cur_link in my_links["data"]:
        cur_item = {}
        if cur_link["{#ONLINE}"]:
            cascade_name = cur_link["{#CASCADENAME}"].split(":")
            if len(cascade_name) > 1:
                cur_item["{#ACCOUNT_NAME}"] = cascade_name[0]
                cur_item["{#TARGET_HOST}"] = cascade_name[1]
                cur_item["{#TARGETHUB}"] = cur_link["{#TARGETHUB}"]
                cur_item["{#HUBNAME}"] = cur_link["{#HUBNAME}"]
                cur_item["{#HOSTNAME}"] = cur_link["{#HOSTNAME}"]
                new_links.append(cur_item)
    my_links["data"] = new_links
    return json.dumps(my_links)

def external_ping_discovery():
    """this is docstring"""
    my_links = json.loads(cascade_discovery())
    new_links = []
    for cur_link in my_links["data"]:
        cur_item = {}
        if cur_link["{#ONLINE}"]:
            cur_item["{#TARGETHUB}"] = cur_link["{#TARGETHUB}"]
            cur_item["{#HUBNAME}"] = cur_link["{#HUBNAME}"]
            cur_item["{#HOSTNAME}"] = cur_link["{#HOSTNAME}"]
            new_links.append(cur_item)
    my_links["data"] = new_links
    return json.dumps(my_links)

def cascade_stats_detailed():
    """
    This is doc string
    :return:
    """
    result_json = {}
    # get hub list
    fn_hubs_dict = json.loads(hub_list())
    fn_hub_list = fn_hubs_dict['result']['HubList']
    for cur_hub_item in fn_hub_list:
        cur_hub_name = cur_hub_item["HubName_str"]
        cur_hub_cascades = json.loads(cascade_list(cur_hub_name))
        json_item = {}
        for cur_item in cur_hub_cascades["result"]["LinkList"]:
            cascade_name = cur_item["AccountName_utf"]
            cur_item_stat = json.loads(get_cascade_status(cur_hub_name, cascade_name))
            if "error" not in cur_item_stat.keys():
                item_converted = convert_bool(cur_item_stat["result"])
                for key, value in item_converted.items():
                    json_item[key] = value
                if cur_hub_name not in result_json.keys():
                    result_json[cur_hub_name] = {cascade_name: json_item}
                else:
                    result_json[cur_hub_name][cascade_name] = json_item
    return json.dumps(result_json)

def cascade_stats():
    """
    This is doc string
    :return:
    """
    result_json = {}
    # get hub list
    fn_hubs_dict = json.loads(hub_list())
    fn_hub_list = fn_hubs_dict['result']['HubList']
    for cur_hub_item in fn_hub_list:
        cur_hub_name = cur_hub_item["HubName_str"]
        cur_hub_cascades = json.loads(cascade_list(cur_hub_name))
        for cur_item in cur_hub_cascades["result"]["LinkList"]:
            json_item = {}
            cascade_name = cur_item["AccountName_utf"]
            item_converted = convert_bool(cur_item)
            for key, value in item_converted.items():
                json_item[key] = value
            if cur_hub_name not in result_json.keys():
                result_json[cur_hub_name] = {cascade_name: json_item}
            else:
                result_json[cur_hub_name][cascade_name] = json_item
    return json.dumps(result_json)

def cascade_stat(p_hub_name, p_cascade_name):
    """
    This is doc string
    :return:
    """
    result_json = {}
    # get hub list
    fn_hubs_dict = json.loads(hub_list())
    fn_hub_list = fn_hubs_dict['result']['HubList']
    for cur_hub_item in fn_hub_list:
        cur_hub_name = cur_hub_item["HubName_str"]
        cur_hub_cascades = json.loads(cascade_list(cur_hub_name))
        json_item = {}
        for cur_item in cur_hub_cascades["result"]["LinkList"]:
            cascade_name = cur_item["AccountName_utf"]
            if (cur_hub_name == p_hub_name) and (cascade_name == p_cascade_name):
                for key, value in cur_item.items():
                    json_item[key] = value
                result_json = json_item
    return json.dumps(result_json)

def get_cascade(hub_name, cascade_name):
    """
    This is doc string
    :return:
    """
    # get hub
    fn_params = {"HubName_Ex_str": str(hub_name),
                 "AccountName_utf": str(cascade_name)}
    fn_method = "GetLinkStatus"
    fn_result = do_request(fn_method, fn_params)
    return json.dumps(fn_result)

def user_list(hub_name):
    """
    This is doc string
    :return:
    """
    # get hub list
    fn_params = {"HubName_str": str(hub_name)}
    fn_method = "EnumUser"
    fn_result = do_request(fn_method, fn_params)
    return json.dumps(fn_result)

def user_discovery():
    """
    This is doc string
    :return:
    """
    zabbix_json = {"data": []}
    # get hub list
    fn_hubs = json.loads(hub_list())
    for cur_hub in fn_hubs["result"]["HubList"]:
        cur_hub_name = cur_hub["HubName_str"]
        fn_users = json.loads(user_list(cur_hub_name))
        for cur_item in fn_users['result']['UserList']:
            item_converted = convert_bool(cur_item)
            json_item = {}
            json_item["{#HUBNAME}"] = cur_hub_name
            json_item["{#USERNAME}"] = item_converted["Name_str"]
            json_item["{#GROUPNAME}"] = item_converted["GroupName_str"]
            json_item["{#REALNAME}"] = item_converted["Realname_utf"]
            json_item["{#NOTE}"] = item_converted["Note_utf"]
            json_item["{#AUTHTYPE}"] = item_converted["AuthType_u32"]
            json_item["{#DENYACCESS}"] = item_converted["DenyAccess_bool"]
            json_item["{#ISTRAFFICFILLED}"] = item_converted["IsTrafficFilled_bool"]
            json_item["{#ISEXPIRESFILLED}"] = item_converted["IsExpiresFilled_bool"]
            json_item["{#EXPIRESDATE}"] = item_converted["Expires_dt"]
            zabbix_json["data"].append(json_item)
    return json.dumps(zabbix_json)

def get_user(hub_name, user_name):
    """
    This is doc string
    :return:
    """
    # get hub
    fn_params = {"HubName_str": str(hub_name),
                 "Name_str": str(user_name)}
    fn_method = "GetUser"
    fn_result = do_request(fn_method, fn_params)
    return json.dumps(fn_result)

def user_stats_detailed():
    """
    This is doc string
    :return:
    """
    result_json = {}
    # get hub list
    fn_hubs_dict = json.loads(hub_list())
    fn_hub_list = fn_hubs_dict['result']['HubList']
    for cur_hub_item in fn_hub_list:
        cur_hub_name = cur_hub_item["HubName_str"]
        cur_hub_users = json.loads(user_list(cur_hub_name))
        json_item = {}
        for cur_item in cur_hub_users["result"]["UserList"]:
            user_name = cur_item["Name_str"]
            cur_item_stat = json.loads(get_user(cur_hub_name, user_name))
            if "error" not in cur_item_stat.keys():
                item_converted = convert_bool(cur_item_stat["result"])
                for key, value in item_converted.items():
                    json_item[key] = value
                if cur_hub_name not in result_json.keys():
                    result_json[cur_hub_name] = {user_name: json_item}
                else:
                    result_json[cur_hub_name][user_name] = json_item
    return json.dumps(result_json)

def user_stats():
    """
    This is doc string
    :return:
    """
    result_json = {}
    # get hub list
    fn_hubs_dict = json.loads(hub_list())
    fn_hub_list = fn_hubs_dict['result']['HubList']
    for cur_hub_item in fn_hub_list:
        cur_hub_name = cur_hub_item["HubName_str"]
        cur_hub_users = json.loads(user_list(cur_hub_name))
        json_item = {}
        for cur_item in cur_hub_users["result"]["UserList"]:
            user_name = cur_item["Name_str"]
            item_converted = convert_bool(cur_item)
            for key, value in item_converted.items():
                json_item[key] = value
            if cur_hub_name not in result_json.keys():
                result_json[cur_hub_name] = {user_name: json_item}
            else:
                result_json[cur_hub_name][user_name] = json_item
    return json.dumps(result_json)

def ping_list(ip_list, ping_count):
    """this is docstring"""
    try:
        # try to set int value from param
        ping_count = int(ping_count)
    except ValueError:
        # if we got not number value
        # we will set default value
        ping_count = PING_COUNT_DEFAULT
    # if ping count > max or < min value
    if ping_count not in range(PING_COUNT_MIN, PING_COUNT_MAX+1):
        # we will set default value
        ping_count = PING_COUNT_DEFAULT
    # result pings dict
    pings_dict = {}
    # generate fping command string (parallel ping to all camera ip's)
    ping_command = "fping -C {} -q ".format(ping_count) + " ".join(ip_list)
    # execute fping and read data (from stderr stream!)
    result = subprocess.run(ping_command.split(' '),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    # get data from stderr stream (decode from utf8 and split into list by '\n'
    result_output = result.stderr.decode('utf-8').split('\n')
    # remove last item (empty string)
    result_output.pop()
    # process lines from list
    for result_line in result_output:
        # exclude lines with 'duplicate for entry'
        if 'duplicate for' in result_line:
            continue
        # split line by space to list of values
        result_line_list = result_line.split(' ')
        # get filter empty values (strings)
        result_line_list = list(filter(lambda x: x != '', result_line_list))
        # get cam ip
        result_line_ip = result_line_list.pop(0)
        # get list of pings
        result_line_data = result_line_list[1:]
        # filter dashes. dash = packet loss
        result_line_pings = list(map(float,
                                     list(filter(lambda x: x != '-',
                                                 result_line_data))))
        if result_line_pings:
            # calculate packet loss %
            result_line_loss = ((len(result_line_data) - len(result_line_pings))
                                / len(result_line_pings)) / 100
            # calculate ping average value
            result_line_avg = float("{0:.2f}".format(sum(result_line_pings) /
                                                     len(result_line_pings)))
            # add ip <-> ping stats item into dictionary
        else:
            result_line_loss = '100'
            result_line_avg = 0
            result_line_pings = [0]
        pings_dict[result_line_ip] = {"min": min(result_line_pings),
                                      "max": max(result_line_pings),
                                      "avg": result_line_avg,
                                      "loss": int(result_line_loss)
                                     }
    return json.dumps(pings_dict)

# get ping statistics
def get_ping(ping_count=PING_COUNT_DEFAULT):
    """this is docstring"""
    # init ip list
    zbx_ips = []
    # result pings
    result_pings = {"external": {},
                    "internal": {}}
    # get hub list
    fn_hubs_dict = json.loads(hub_list())
    for cur_hub_item in fn_hubs_dict['result']['HubList']:
        cur_hub_cascades = json.loads(cascade_list(cur_hub_item["HubName_str"]))
        for cur_item in cur_hub_cascades["result"]["LinkList"]:
            # if cascade is up
            if cur_item["Connected_bool"] and cur_item["Online_bool"]:
                if cur_item["Hostname_str"] not in zbx_ips:
                    zbx_ips.append(cur_item["Hostname_str"])
                    result_pings["external"][cur_item["Hostname_str"]] = {}
                acc_name_splitted = cur_item["AccountName_utf"].split(':')
                if len(acc_name_splitted) > 1:
                    if acc_name_splitted[1] not in zbx_ips:
                        result_pings["internal"][acc_name_splitted[1]] = {}
                        zbx_ips.append(acc_name_splitted[1])
    my_pings = json.loads(ping_list(zbx_ips, ping_count))
    for cur_ip, cur_val in my_pings.items():
        if cur_ip not in result_pings["external"].keys():
            result_pings["internal"][cur_ip] = cur_val
        else:
            result_pings["external"][cur_ip] = cur_val
    # return result json
    return json.dumps(result_pings)

# boolean flag
EXIT_NOW = False

# if we have 1 argument
if len(sys.argv) == 1:
    # script executed without any params
    # activate exit_now flag
    EXIT_NOW = True
    print("Script parameter not set")
# if we got wrong parameter
elif sys.argv[1] not in VALID_COMMANDS:
    print("Wrong script parameter: {}".format(sys.argv[1]))
    EXIT_NOW = True
# if we got exit_now = True
if EXIT_NOW:
    # print default message
    print("Usage: python3 {} ".format(sys.argv[0]) + "|".join(VALID_COMMANDS))
    # exit with errors
    exit(1)

# we need to create a callable expression
# we have our set of methods in VALID_COMMANDS list
# our commands has dots in their names, but our functions has underlines
# we need to replace all '.' to '_' and then add any parameters and call it (evaluate)
# 1. step. split our method name to list of spring. (split character: '.')
METHOD = sys.argv[1].split('.')
# 2. step. we need to generate our function name. concatenate our string list with '_' symbol
METHOD = "_".join(METHOD)
# if we got two arguments
if len(sys.argv) == 2:
    # call function with no parameters
    # we just add () to the end
    METHOD = METHOD + '()'
elif len(sys.argv) == 4:
    if (sys.argv[2] != "") and (sys.argv[3] != ""):
        # call with three params
        # we need to add both parameters between brackets splitted by comma
        METHOD = METHOD + '(' + sys.argv[2] + ', ' + sys.argv[3] + ')'
    else:
        # we need to add brackets
        METHOD = METHOD + '()'
else:
    # we got only one parameter. put it between brackets
    METHOD = METHOD + '(' + sys.argv[2] + ')'
# execute and print
print(eval(METHOD))
# exit
exit(0)
