#!/usr/bin/env python3
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=(root/'build/forth_runtime.elf').read_bytes()
out=root/'extension/forth_runtime_blob.h'
rows=[]
for i in range(0,len(p),16): rows.append(','.join(f'0x{x:02x}' for x in p[i:i+16]))
out.write_text('static const unsigned char forth_runtime_blob[] = {\n'+',\n'.join(rows)+'\n};\n#define FORTH_RUNTIME_SIZE '+str(len(p))+'\n',encoding='ascii')
print('embedded',len(p),'bytes')