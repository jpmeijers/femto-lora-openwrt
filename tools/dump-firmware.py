#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Stream read-only MTD partition backups over SSH to private local gzip files.

Data-only reads use the device's native ECC handling. --raw-oob requires the
rawdump tool from this project's RAM image and streams one eraseblock at a
time, so a full-chip capture never has to fit in gateway RAM. Neither method
is a proven factory rollback procedure. All resulting files are sensitive.
"""
import argparse,gzip,hashlib,json,os,re,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--target',required=True,help='Existing SSH destination, e.g. root@host')
p.add_argument('--output',type=Path,required=True,help='Fresh private directory')
p.add_argument('--raw-oob',action='store_true',help='Also capture eraseblock-sized raw+OOB chunks using rawdump')
p.add_argument('--partition',type=int,action='append',help='MTD index to include; default is all listed partitions')
a=p.parse_args()
if not re.fullmatch(r'[A-Za-z0-9_@.\[\]:-]+',a.target) or a.target.startswith('-'):p.error('Invalid SSH destination')
if a.output.exists():p.error('Use a fresh output directory; existing dumps are never overwritten')
a.output.mkdir(parents=True,mode=0o700)
ssh=['ssh','-T','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','ServerAliveInterval=10','-o','ServerAliveCountMax=3',a.target]
def query(command):return subprocess.check_output(ssh+[command],timeout=30)
if a.raw_oob:
 try:query('command -v rawdump >/dev/null')
 except subprocess.CalledProcessError:raise SystemExit('--raw-oob requires rawdump from this project RAM recovery image')
mtd=query('cat /proc/mtd');(a.output/'proc-mtd.txt').write_bytes(mtd)
partitions=[]
for n,size,erase,label in re.findall(rb'^mtd(\d+): ([0-9a-fA-F]+) ([0-9a-fA-F]+) "([^"\r\n]+)"$',mtd,re.M):
 index=int(n)
 if a.partition and index not in a.partition:continue
 partitions.append((index,int(size,16),int(erase,16),label.decode(errors='replace')))
if not partitions:raise SystemExit('No matching MTD partitions')
manifest={'format':'MTD read-only backup; NOT a factory restore recipe','partitions':[]}
for index,size,erase,label in partitions:
 safe=re.sub(r'[^A-Za-z0-9_.-]','_',label);stem=f'mtd{index:02d}-{safe}'
 record={'index':index,'label':label,'data_bytes':size,'eraseblock_bytes':erase}
 modes=['data']+(['raw-oob'] if a.raw_oob else [])
 for mode in modes:
  final=a.output/f'{stem}.{mode}.bin.gz';partial=final.with_suffix(final.suffix+'.partial')
  sha=hashlib.sha256();total=0
  with partial.open('xb') as output:
   os.chmod(partial,0o600)
   with gzip.GzipFile(filename='',mode='wb',compresslevel=1,fileobj=output,mtime=0) as gz:
    if mode=='data':commands=[(f'cat /dev/mtd{index}',size)]
    else:
     # Reading a block includes every page's OOB. Never skip bad blocks.
     # rawdump validates the actual 2048/64 geometry before creating output.
     raw_size=erase//2048*2112
     commands=[(f'test ! -e /tmp/femto-rawdump-chunk && rawdump /dev/mtd{index} /tmp/femto-rawdump-chunk {erase} {off} && cat /tmp/femto-rawdump-chunk && rm /tmp/femto-rawdump-chunk',raw_size) for off in range(0,size,erase)]
    for command,expected in commands:
     count=0
     with tempfile.TemporaryFile() as errors:
      proc=subprocess.Popen(ssh+[command],stdout=subprocess.PIPE,stderr=errors)
      try:
       while True:
        chunk=proc.stdout.read(65536)
        if not chunk:break
        gz.write(chunk);sha.update(chunk);count+=len(chunk)
       code=proc.wait()
      except BaseException:
       proc.kill();proc.wait();raise
      if code or count!=expected:
       errors.seek(0);(a.output/f'{stem}.{mode}.error.txt').write_bytes(errors.read())
       raise SystemExit(f'mtd{index} {mode}: incomplete read; retained .partial, no complete manifest. If rawdump was interrupted, inspect/remove only /tmp/femto-rawdump-chunk before retrying.')
     total+=count
  partial.rename(final)
  record[mode]={'file':final.name,'bytes':total,'sha256_uncompressed':sha.hexdigest()}
  print(f'Captured mtd{index} {mode}: {total} bytes',flush=True)
 manifest['partitions'].append(record)
 # Partial metadata is explicitly distinct from the final complete manifest.
 (a.output/'manifest.partial.json').write_text(json.dumps(manifest,indent=2)+'\n')
(a.output/'manifest.partial.json').rename(a.output/'manifest.json')
print('Complete. Keep all dumps private; these do not establish factory rollback.')
