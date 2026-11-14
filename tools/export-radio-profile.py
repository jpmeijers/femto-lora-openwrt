#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-only
"""Whitelist non-identifying radio fields from a private femto-board-info JSON.

Example: ssh root@host femto-board-info > private/board-info.json
         python3 tools/export-radio-profile.py private/board-info.json > radio-profile.json
Never upload the input JSON, configuration backups or full firmware dumps.
"""
import argparse,json,math
p=argparse.ArgumentParser(description=__doc__);p.add_argument('input');a=p.parse_args()
with open(a.input) as f:src=json.load(f)
region=src.get('region');band=src.get('eeprom_band')
if region not in ['EU','NON_EU','UNKNOWN'] or band is not None and (type(band)!=int or not 0<=band<=255):raise SystemExit('Invalid radio metadata')
keys=['dig_gain','pa_gain','dac_gain','mix_gain','rf_power'];lut=[]
for row in src.get('tx_lut',[]):
 if len(lut)>=16 or any((type(row.get(k)) not in [int,float] or not math.isfinite(row[k])) for k in keys):raise SystemExit('Invalid numeric gain table')
 lut.append({k:row[k] for k in keys})
print(json.dumps({'region':region,'eeprom_band':band,'tx_lut':lut},indent=2))
