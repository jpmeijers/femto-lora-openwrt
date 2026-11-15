#!/usr/bin/env python3
"""Isolated LED policy checks on OpenWrt; all GPIO/proc inputs are fixtures.

Requires SSH key/agent access. --script can test a local monitor before install.
No persistent settings, live LEDs, radio processes or credentials are changed.
"""
import argparse,json,re,shlex,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--target',required=True);p.add_argument('--script',type=Path);a=p.parse_args()
if not re.fullmatch(r'[A-Za-z0-9_@.\[\]:-]+',a.target) or a.target.startswith('-'):p.error('Invalid target')
ssh=['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=10',a.target]
def run(cmd,data=None):
 r=subprocess.run(ssh+[cmd],input=data,capture_output=True,timeout=25)
 if r.returncode:raise RuntimeError('LED fixture command failed: '+r.stderr.decode(errors='replace'))
 return r.stdout
root=run('mktemp -d /tmp/femto-led-fixtures.XXXXXX').decode().strip();q=shlex.quote(root)
def put(path,content):run('cat > '+shlex.quote(root+'/'+path),(json.dumps(content) if not isinstance(content,str) else content).encode())
def config(enabled='1',protocol='basicstation',automatic='1'):
 put('config/lorawan',f"config gateway 'main'\n option enabled '{enabled}'\n option protocol '{protocol}'\n")
 put('config/femto-leds',f"config indicators 'main'\n option enabled '{automatic}'\n option probe_host ''\n")
def marker(kind,active=1,pid=4242,since=1995):put('run/lorawan/'+kind+'.json',dict(pid=pid,since=since,active=active))
def status():return json.loads(run('ucode '+q+'/monitor.uc --once'))
try:
 run('mkdir -p '+q+'/config '+q+'/run/lorawan '+q+'/proc/4242/fd '+q+'/proc/net '+q+'/sys/class/net/wlan-fixture')
 put('proc/uptime','2000.0 0.0\n');put('proc/net/tcp6','')
 put('proc/net/tcp','0: 0100007F:1234 0200007F:22B7 01 0:0 0:0 0 0 0 4242\n')
 run('ln -s '+shlex.quote('socket:[4242]')+' '+q+'/proc/4242/fd/1; ln -s /usr/sbin/femto-basicstation '+q+'/proc/4242/exe')
 for icon in ['internet','wifi','lora']:
  for colour in ['green','amber']:
   name='sys/class/leds/'+colour+':'+icon;run('mkdir -p '+shlex.quote(root+'/'+name));put(name+'/brightness','0');put(name+'/trigger','[none]')
 wireless={'radio0':{'up':True,'disabled':False,'interfaces':[{'ifname':'wlan-fixture','config':{'mode':'sta'}}]}}
 put('wireless.json',wireless);put('sys/class/net/wlan-fixture/operstate','up\n')
 source=a.script.read_text() if a.script else run('cat /usr/sbin/femto-leds').decode()
 source=source.replace('cursor()',f'cursor({json.dumps(root+"/config")})')
 source=source.replace('/var/run/',root+'/run/').replace('/proc/',root+'/proc/').replace('/sys/',root+'/sys/')
 source=source.replace("let wireless = bus ? bus.call('network.wireless', 'status', {}) : {};",f"let wireless = readjson('{root}/wireless.json');")
 put('monitor.uc',source);config();marker('station-link',since=1900);marker('station-radio')
 s=status();assert s['lora']=='green' and s['internet']=='green' and s['wifi']=='green',s
 marker('station-link',active=0);assert status()['lora']=='amber'
 marker('station-link',since=1900);marker('station-radio',active=0);assert status()['lora']=='amber'
 marker('station-radio');put('proc/net/tcp','0: 0100007F:1234 0200007F:22B7 01 0:0 0:0 0 0 0 9999\n');assert status()['lora']=='amber','Unowned socket accepted'
 put('proc/net/tcp','0: 0100007F:1234 0200007F:22B7 01 0:0 0:0 0 0 0 4242\n')
 marker('station-link',pid=9999);assert status()['lora']=='amber','Dead process accepted'
 marker('station-link',since=1900);put('sys/class/net/wlan-fixture/operstate','down\n');assert status()['wifi']=='amber'
 wireless['radio0']['disabled']=True;put('wireless.json',wireless);assert status()['wifi']=='off'
 config(protocol='udp');run('rm '+q+'/proc/4242/exe; ln -s /usr/sbin/lora_pkt_fwd '+q+'/proc/4242/exe')
 marker('udp-radio',since=1900);marker('udp-pull-ack');assert status()['lora']=='green'
 marker('udp-pull-ack',since=1800);assert status()['lora']=='amber','Stale ACK accepted'
 marker('udp-pull-ack',pid=9999);assert status()['lora']=='amber','Wrong-process ACK accepted'
 config(enabled='0');assert status()['lora']=='off'
 config(automatic='0');put('sys/class/leds/green:lora/brightness','7');status();assert run('cat '+q+'/sys/class/leds/green:lora/brightness')==b'7'
 print('LED policies passed: connected/radio-ready, owned sockets, dead processes, fresh/stale UDP ACKs, Wi-Fi, disabled functions and manual control.')
finally:run('rm -rf '+q)
