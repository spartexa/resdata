import re, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GEN = os.path.join(ROOT, 'dotnet_bindings', 'src', 'Generated')
keywords = ['string','int','double','float','bool','long','char']
pattern = re.compile(r"\b({0})\s+\1\b".format('|'.join(keywords)))

for dp, dn, fn in os.walk(GEN):
    for f in fn:
        if not f.endswith('.cs'):
            continue
        path = os.path.join(dp, f)
        with open(path, 'r', encoding='utf-8') as fh:
            txt = fh.read()
        new = pattern.sub(lambda m: f"{m.group(1)} @{m.group(1)}", txt)
        if new != txt:
            with open(path, 'w', encoding='utf-8') as fh:
                fh.write(new)
            print('Fixed', path)
print('Done')
