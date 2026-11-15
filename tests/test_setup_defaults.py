#!/usr/bin/env python3
"""Check fresh/reset setup defaults and upgrade preservation in isolated UCI files."""
import argparse,re,shlex,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--target',required=True);p.add_argument('--script',type=Path);a=p.parse_args()
if not re.fullmatch(r'[A-Za-z0-9_@.\[\]:-]+',a.target) or a.target.startswith('-'):p.error('Invalid target')
ssh=['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=10',a.target]
def run(cmd,data=None,check=True):
 r=subprocess.run(ssh+[cmd],input=data,capture_output=True,timeout=25)
 if check and r.returncode:raise RuntimeError(r.stderr.decode(errors='replace'))
 return r
root=run('mktemp -d /tmp/femto-setup-fixtures.XXXXXX').stdout.decode().strip();q=shlex.quote(root)
def put(name,data):run('cat > '+shlex.quote(root+'/'+name),data.encode())
def get(key):return run('/sbin/uci -c '+q+'/config -q get '+shlex.quote(key)).stdout.decode().strip()
def snapshot():return run('sha256sum '+q+'/config/*').stdout
try:
 run('mkdir -p '+q+'/bin '+q+'/config')
 source=a.script.read_text() if a.script else run('cat /usr/sbin/femto-setup-defaults').stdout.decode()
 source=source.replace('/sys/class/ieee80211/phy0/macaddress',root+'/macaddress');put('defaults.sh',source)
 put('bin/uci','#!/bin/sh\nexec /sbin/uci -c '+q+'/config "$@"\n');put('bin/wifi','#!/bin/sh\nexit 0\n');run('chmod +x '+q+'/bin/*')
 mac=bytes([2,17,34,51,68,85]);put('macaddress',':'.join(f'{x:02x}' for x in mac)+'\n')
 def fresh(pending=True,radio=True):
  put('config/network',"config interface 'lan'\n option ipaddr '192.168.88.10'\n"+("config femto_setup 'femto_defaults'\n option pending '1'\n" if pending else ''))
  put('config/wireless',"config wifi-device 'radio0'\n option disabled '1'\nconfig wifi-iface 'default_radio0'\n option ssid 'OpenWrt'\n" if radio else '')
  put('config/dhcp',"config dnsmasq\nconfig dhcp 'lan'\n option interface 'lan'\n option ignore '1'\n")
  put('config/firewall',"config zone 'lan'\n option name 'lan'\n list network 'lan'\n")
 def apply():return run('PATH='+q+'/bin:/usr/sbin:/usr/bin:/sbin:/bin sh '+q+'/defaults.sh',check=False)
 fresh(pending=False);before=snapshot();assert apply().returncode==0 and before==snapshot(),'Preserved configuration changed'
 fresh(radio=False);before=snapshot();assert apply().returncode and before==snapshot() and get('network.femto_defaults.pending')=='1'
 fresh();assert apply().returncode==0
 assert get('network.lan.ipaddr')=='192.168.88.10' and get('network.setup.ipaddr')=='192.168.89.1'
 assert get('network.setup.device')=='br-setup' and get('network.setup_bridge.type')=='bridge'
 assert get('wireless.femto_setup.ssid')=='Femto-Setup-'+mac.hex()[-6:]
 assert get('wireless.femto_setup.encryption')=='none' and get('wireless.femto_setup.network')=='setup'
 assert get('wireless.radio0.disabled')=='0'
 assert get('dhcp.lan.ignore')=='1' and get('dhcp.setup.interface')=='setup' and get('dhcp.setup.ignore')=='0'
 assert get('dhcp.setup.dhcp_option')=='3','Setup advertises a default route'
 assert get('firewall.femto_setup.network')=='setup' and get('firewall.femto_setup.forward')=='REJECT'
 assert run('/sbin/uci -c '+q+'/config -q get network.femto_defaults',check=False).returncode
 before=snapshot();assert apply().returncode==0 and before==snapshot(),'Defaults are not idempotent'
 print('Setup defaults passed: preserve upgrades, retry missing radio, isolated AP/DHCP, no default route, firewall isolation and idempotence.')
finally:run('rm -rf '+q)
