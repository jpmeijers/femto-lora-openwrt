#!/usr/bin/env python3
"""Exercise the installed ucode generator in temporary files on an OpenWrt host.

Requires a matching running development image, SSH key/agent access, and the
updated generator installed. No persistent settings or radio service changes.
Example: python3 tests/test_station_config.py --target root@gateway
"""
import argparse,json,re,shlex,subprocess
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--target',required=True);a=p.parse_args()
if not re.fullmatch(r'[A-Za-z0-9_@.\[\]:-]+',a.target) or a.target.startswith('-'):p.error('Invalid SSH target')
ssh=['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=10',a.target]
def run(cmd,data=None,check=True):
 r=subprocess.run(ssh+[cmd],input=data,capture_output=True,timeout=30)
 if check and r.returncode:raise RuntimeError('Remote configuration test failed (output withheld)')
 return r
root=run('mktemp -d /tmp/femto-station-test.XXXXXX').stdout.decode().strip();q=shlex.quote(root)
try:
 run('mkdir '+q+'/config '+q+'/run')
 source=run('cat /usr/sbin/femto-lora-config').stdout.decode()
 source=source.replace('cursor()',f'cursor({json.dumps(root+"/config")})').replace('/var/run/lorawan',root+'/run')
 source=source.replace("popen('/usr/sbin/femto-board-info', 'r')",f"popen('cat {root}/board.json', 'r')")
 run('cat > '+q+'/config.uc',source.encode())
 # Build a synthetic, non-identifying EUI without embedding a real unit ID.
 eui=bytes(range(1,9)).hex().upper()
 board={'region':'EU','eui':eui,'tx_lut':[]}
 run('cat > '+q+'/board.json',json.dumps(board).encode())
 run('cat > '+q+'/config/lorawan',run('cat /etc/lorawan-test-defaults 2>/dev/null || cat /rom/etc/config/lorawan').stdout)
 uci='uci -c '+q+'/config '
 def setting(k,v):run(uci+'set '+shlex.quote('lorawan.main.'+k+'='+v)+'; '+uci+'commit lorawan')
 def generate():return run('ucode '+q+'/config.uc',check=False)
 setting('gateway_id','');setting('advanced','');setting('protocol','basicstation');setting('lns_key','')
 assert generate().returncode,'Missing key accepted'
 setting('lns_key','TEST_ONLY_NOT_A_TTN_KEY');setting('lns_uri','ws://example.invalid:8887')
 assert generate().returncode,'Plaintext LNS accepted'
 setting('lns_uri','wss://example.invalid:8887');assert generate().returncode==0
 c=json.loads(run('cat '+q+'/run/station.conf').stdout)
 assert c['station_conf']['routerid']==eui and c['station_conf']['euiprefix']=='::0'
 assert c['station_conf']['RADIO_INIT_WAIT']=='5s'
 rf=c['SX1301_conf'];assert len(rf['tx_gain_lut'])==16
 assert all(row['dac_gain']==3 and isinstance(row['rf_power'],int) for row in rf['tx_gain_lut'])
 assert all('freq' not in rf['radio_'+str(i)] for i in range(2)), 'Local frequency masks LNS plan'
 assert run('cat '+q+'/run/tc.key').stdout==b'Authorization: Bearer TEST_ONLY_NOT_A_TTN_KEY\r\n'
 assert b'rw-------' in run('ls -l '+q+'/run/tc.key').stdout
 for region,conflict in [('NON_EU',False),('EU',True),('UNKNOWN',False)]:
  run('cat > '+q+'/board.json',json.dumps(dict(board,region=region,region_conflict=conflict)).encode())
  assert generate().returncode,'Unsupported metadata accepted'
 print('Station EUI, LNS/TLS/token guards, gain conversion, reset timeout and region checks passed.')
finally:run('rm -rf '+q)
