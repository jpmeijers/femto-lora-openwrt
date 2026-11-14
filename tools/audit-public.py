#!/usr/bin/env python3
"""Audit staged public files; optionally scan an extracted rootfs and private needles.

--forbidden-file is an ignored local newline-separated list of identifiers or
credentials. Matches are reported by filename only, never by secret value.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--rootfs', type=Path)
p.add_argument('--require-basicstation', action='store_true')
p.add_argument('--forbidden-file', type=Path)
a = p.parse_args()
allowed_files = {'.gitignore', '.gitattributes', 'README.md', 'LICENSE', 'NOTICE.md', 'requirements.txt'}
allowed_dirs = {'board', 'docs', 'tools', 'firmware', 'tests'}
needles = []
if a.forbidden_file:
    needles = [x for x in a.forbidden_file.read_bytes().splitlines() if len(x) >= 6]
private_key = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----\s+[A-Za-z0-9+/=\r\n]{40,}-----END')
actual_eui = re.compile(rb'(?:gateway_id\s+\x27|"gateway_ID"\s*:\s*")[0-9a-fA-F]{16}')
mac = re.compile(rb'(?i)(?<![0-9a-f])(?:[0-9a-f]{2}:){5}[0-9a-f]{2}(?![0-9a-f])')
errors = []
def inspect(name, data, source=False):
    if private_key.search(data): errors.append((name, 'private-key material'))
    if source and actual_eui.search(data): errors.append((name, 'literal gateway EUI'))
    if source and mac.search(data): errors.append((name, 'literal MAC address; review required'))
    for value in needles:
        if value.lower() in data.lower():
            errors.append((name, 'private audit value'))
            break

files = subprocess.check_output(['git', 'ls-files', '-z']).decode().split('\0')
for name in filter(None, files):
    path = Path(name)
    if name not in allowed_files and path.parts[0] not in allowed_dirs:
        errors.append((name, 'outside public allowlist'))
    if '__pycache__' in path.parts or 'python-deps' in path.parts:
        errors.append((name, 'generated/local dependency'))
    data = subprocess.check_output(['git', 'show', ':' + name])
    inspect(name, data, not name.endswith('.bin') and not name.endswith('.ubi'))
if a.rootfs:
    for path in a.rootfs.rglob('*'):
        if path.is_symlink() or not path.is_file(): continue
        data = path.read_bytes()
        inspect(str(path), data)
        if data and (path.name.startswith('dropbear_') and path.name.endswith('_host_key') or path.name == 'uhttpd.key'):
            errors.append((str(path), 'nonempty generated host private key'))
    conf = (a.rootfs / 'etc/config/lorawan').read_text()
    if "option gateway_id ''" not in conf: errors.append(('lorawan', 'default EUI is not blank'))
    if a.require_basicstation:
        if not (a.rootfs / 'usr/sbin/femto-basicstation').is_file(): errors.append(('rootfs', 'Basic Station missing'))
        if "option lns_key ''" not in conf: errors.append(('lorawan', 'default LNS key is not blank'))
        if "option enabled '0'" not in conf: errors.append(('lorawan', 'forwarding enabled in generic image'))
        if not (a.rootfs / 'etc/ssl/certs/ca-certificates.crt').is_file(): errors.append(('rootfs', 'CA bundle missing'))
    plan = json.loads((a.rootfs / 'usr/share/lorawan/eu868.json').read_text())
    if plan['gateway_conf']['gateway_ID']: errors.append(('eu868.json', 'default EUI is not blank'))
    if len([k for k in plan['SX1301_conf'] if k.startswith('tx_lut_')]) != 16: errors.append(('eu868.json', 'missing EU reference gain table'))
    if not plan['SX1301_conf']['radio_0']['tx_enable']: errors.append(('eu868.json', 'EU TX default unexpectedly disabled'))
if errors:
    for name, why in errors: print(f'FAIL: {name}: {why}')
    raise SystemExit(1)
print('Public staged-file and firmware privacy checks passed.')
