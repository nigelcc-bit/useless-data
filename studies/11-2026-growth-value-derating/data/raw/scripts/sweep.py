import json,glob,re,os,base64,gzip
for p in glob.glob('/tmp/claude-tool-results/*/mcp-remote-devices-Claude_Browser__javascript_tool-*.txt'):
    try:
        o=json.load(open(p)); t=o[0]['text']
        if t.startswith('"'): t=t[1:]
        m=re.match(r'([A-Za-z0-9_\-]+)\|(\d+)\|(\d+)#',t)
        if not m: continue
        body=t[m.end():]; body=body.split('"')[0].split('\n')[0].strip()
        open(f'chunks/{m[1]}.{int(m[2]):03d}.{m[3]}','w').write(body)
    except Exception as e: pass
done={}
for f in sorted(glob.glob('chunks/*')):
    k,i,n=f.split('/')[-1].rsplit('.',2); done.setdefault((k,int(n)),set()).add(int(i))
for (k,n),s in sorted(done.items()):
    missing=sorted(set(range(n))-s)
    print(k,n,'missing',missing)
    if not missing and not os.path.exists(f'out/{k}.bin'):
        os.makedirs('out',exist_ok=True)
        b=''.join(open(f'chunks/{k}.{i:03d}.{n}').read() for i in range(n))
        raw=gzip.decompress(base64.b64decode(b)); open(f'out/{k}.bin','wb').write(raw); print('  assembled',k,len(raw))
