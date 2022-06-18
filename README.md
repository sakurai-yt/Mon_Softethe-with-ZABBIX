# sevpn_zabbix
SoftEther VPN server monitoring with zabbix.
Monitoring by API with python3 script.

__REQUIREMENTS__
- `fping` system utility
- `zabbix` 5.0 or above 100% compability
- `python3` with packages: requests (pip3 install requests) (tested only with python3!)
- `Amazon Linux2` 
- `SoftEtherVPN` only with REST API features. Tested on beta v4.34 build 9745

__INSTALLATION__
In my example i have installed zabbix 5.0 agent in /etc/zabbix directory.
Scripts directory: /etc/zabbix/scripts (if your path different then edit sevpn.conf file!)

- Copy sevpn.py & sevpn.ini to scripts directory
- Copy sevpn.conf file to zabbix_agentd.d directory
- Install packages ```yum install python3```
- Install python packages ```pip3 install requests```
- Inport zbx_templates
- Restart zabbix agent

__CONFIGURE & TEST__
- Set ADMIN_PASS - admin password
Optional:
- Set URL
- Set PORT

This script tested only for admin account.

- Run ```sudo -u zabbix zabbix_agentd -t sevpn[hub.discovery]```

You will see valid JSON object.
