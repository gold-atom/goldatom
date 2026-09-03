#!/usr/bin/env node
// Independent raw-record scanner. Does not import or invoke Python.
import fs from 'node:fs'; import crypto from 'node:crypto';
const dsha=b=>crypto.createHash('sha256').update(crypto.createHash('sha256').update(b).digest()).digest();
const display=h=>Buffer.from(dsha(h)).reverse().toString('hex');
const value=h=>BigInt('0x'+display(h));
function compact(bits){const e=bits>>>24,m=bits&0x007fffff;if(bits&0x00800000)throw Error('negative compact');return e<=3?BigInt(m)>>BigInt(8*(3-e)):BigInt(m)<<BigInt(8*(e-3));}
export function scanBuffer(data){if(data.length%80)throw Error('bad length');let frontier=null;const records=[];for(let height=0;height<data.length/80;height++){const h=data.subarray(height*80,height*80+80);const hash=display(h),v=value(h),bits=h.readUInt32LE(72),target=compact(bits);if(height===0&&hash!=='000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f')throw Error('genesis');if(height){const prev=Buffer.from(h.subarray(4,36)).reverse().toString('hex');const ph=display(data.subarray((height-1)*80,height*80));if(prev!==ph)throw Error(`link ${height}`);}if(v>target)throw Error(`pow ${height}`);if(frontier===null||v<frontier){records.push({height,hash});frontier=v;}}
return {records,count:records.length,frontier:frontier.toString(16).padStart(64,'0'),tip_height:data.length/80-1,tip_hash:display(data.subarray(data.length-80))};}
if(process.argv[1]&&import.meta.url===new URL('file://'+process.argv[1]).href){const r=scanBuffer(fs.readFileSync(process.argv[2]));console.log(JSON.stringify(r,null,2));}
