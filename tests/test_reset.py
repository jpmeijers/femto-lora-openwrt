#!/usr/bin/env python3
"""Test reset thresholds with stubbed erase/reboot commands in temporary files."""
import argparse,re,shlex,subprocess
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--target',required=True);p.add_argument('--script',type=Path);a=p.parse_args()
if not re.fullmatch(r'[A-Za-z0-9_@.\[\]:-]+',a.target) or a.target.startswith('-'):p.error('Invalid target')
ssh=['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=10',a.target]
def run(cmd,data=None,check=True):
 r=subprocess.run(ssh+[cmd],input=data,capture_output=True,timeout=25)
 if check and r.returncode:raise RuntimeError(r.stderr.decode(errors='replace'))
 return r
root=run('mktemp -d /tmp/femto-reset-fixtures.XXXXXX').stdout.decode().strip();q=shlex.quote(root)
def put(name,data):run('cat > '+shlex.quote(root+'/'+name),data.encode())
try:
 run('mkdir -p '+q+'/bin')
 src=a.script.read_text() if a.script else run('cat /usr/sbin/femto-reset-button').stdout.decode()
 src=src.replace('/proc/mounts',root+'/mounts').replace('/etc/diag.sh',root+'/diag.sh');put('reset.sh',src)
 put('diag.sh','set_state() { echo "led:$1" >> '+q+'/trace; }\n')
 for name in ['logger','sync','reboot','jffs2reset']:
  put('bin/'+name,'#!/bin/sh\necho '+shlex.quote(name)+' >> '+q+'/trace\n'+('exit "${ERASE_STATUS:-0}"\n' if name=='jffs2reset' else 'exit 0\n'))
 run('chmod +x '+q+'/bin/*')
 def event(action,seen='0',mounted=True,erase_status=0):
  put('mounts','/dev/ubi0_1 /overlay ubifs rw 0 0\n' if mounted else '')
  put('trace','')
  cmd='PATH='+q+'/bin:/usr/sbin:/usr/bin:/sbin:/bin ACTION='+shlex.quote(action)+' SEEN='+shlex.quote(str(seen))+' ERASE_STATUS='+str(erase_status)+' sh -c '+shlex.quote('. '+root+'/reset.sh')
  r=run(cmd,check=False);trace=run('cat '+q+'/trace').stdout.decode().splitlines();return r.returncode,trace
 assert event('pressed')[0]==10
 assert event('pressed',mounted=False)==(0,[])
 code,trace=event('timeout');assert code==0 and 'led:failsafe' in trace and 'jffs2reset' not in trace
 for seen in [1,5,9,'not-a-number']:
  code,trace=event('released',seen);assert 'jffs2reset' not in trace and 'reboot' not in trace
 code,trace=event('released',0);assert 'reboot' in trace and 'jffs2reset' not in trace
 for seen in [10,30]:
  code,trace=event('released',seen);assert trace.index('jffs2reset')<trace.index('reboot')
 assert event('released',10,mounted=False)==(0,[])
 code,trace=event('released',10,erase_status=1);assert 'jffs2reset' in trace and 'reboot' not in trace
 print('Reset tests passed: arm timeout, short reboot, ignored holds, long reset, RAM guard and failed-erase behavior.')
finally:run('rm -rf '+q)
