# -*- coding: utf-8 -*-
import re
import pathlib

src = pathlib.Path(r'e:\lianping\408\.trae\index.js').read_text(encoding='utf-8')
found = set()
for m in re.finditer(r'[\w\-]*[Ee]xercise[\w\-]*\.js', src):
    found.add('CHUNK: ' + m.group(0))
for m in re.finditer(r'["\'][/"A-Za-z0-9_\-]*hint[A-Za-z0-9_/\-]*["\']', src):
    found.add('HINT: ' + m.group(0))
for m in re.finditer(r'["\']/api/[^"\']+["\']', src):
    found.add('API: ' + m.group(0))
for line in sorted(found):
    print(line)
