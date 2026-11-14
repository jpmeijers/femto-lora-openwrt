#!/usr/bin/env python3
"""Synthetic metadata fixtures only: no development gateway identifiers."""
import json,struct,subprocess,tempfile,unittest,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class BoardInfo(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.root=Path(cls.tmp.name);cls.exe=cls.root/'board-info'
  subprocess.run(['cc','-std=c99','-D_XOPEN_SOURCE=700','-Wall','-Wextra','-Werror','-O2',str(ROOT/'openwrt/package/utils/femto-lorawan/src/board-info.c'),'-o',str(cls.exe)],check=True)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def read(self,country='EU',band=1,valid=True,cache=True,local=False):
  ee=bytearray([255]*126);ee[:8]=bytes([0,0,0x10,0x20,0x30,0x40,0x50,0x60]);ee[8]=band;ee[14:16]=bytes([3,3])
  for i in range(16):ee[16+4*i:20+4*i]=bytes([i%4,i%4,8+i%8,2*i])
  fields=[b'bootcmd=example',b'lora_country_code='+country.encode()]
  if cache:fields.append(b'lora_ee_cnt_0='+ee.hex().encode())
  data=b'\0'.join(fields)+b'\0\0';data=data.ljust(4092,b'\0');crc=zlib.crc32(data)^(0 if valid else 1)
  c=self.root/'config';c.write_bytes(struct.pack('<I',crc)+data)
  f=self.root/'factory';mac=bytes([2 if local else 0,0x12,0x24,0x36,0x48,0x5a]);f.write_bytes(bytes(4)+mac)
  r=json.loads(subprocess.check_output([str(self.exe),'--config',str(c),'--factory',str(f)]))
  return r,ee,mac
 def test_factory_cache(self):
  r,ee,_=self.read();self.assertEqual(r['eui'],ee[:8].hex().upper());self.assertEqual(r['region'],'EU');self.assertTrue(r['config_crc_valid']);self.assertEqual(len(r['tx_lut']),16)
 def test_invalid_crc_falls_back(self):
  r,_,m=self.read(valid=False);expected=bytes([m[0]|2])+m[1:3]+bytes([255,254])+m[3:]
  self.assertEqual(r['eui'],expected.hex().upper());self.assertEqual(r['region'],'UNKNOWN');self.assertFalse(r['config_crc_valid']);self.assertEqual(r['tx_lut'],[])
 def test_local_bit_is_not_toggled(self):
  r,_,_=self.read(cache=False,local=True);self.assertEqual(int(r['eui'][:2],16)&2,2);self.assertEqual(r['eui'][6:10],'FFFE')
 def test_non_eu(self):
  r,_,_=self.read(country='US',band=0);self.assertEqual(r['region'],'NON_EU');self.assertFalse(r['region_conflict'])
 def test_conflict(self):
  r,_,_=self.read(country='EU',band=0);self.assertTrue(r['region_conflict']);self.assertEqual(r['region'],'NON_EU')
 def test_unknown_is_not_guessed(self):
  r,_,_=self.read(country='',band=255);self.assertEqual(r['region'],'UNKNOWN')
if __name__=='__main__':unittest.main()
