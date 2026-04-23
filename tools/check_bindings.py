import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
GENERATED_DIR = os.path.join(ROOT, 'dotnet_bindings', 'src', 'Generated')
MANIFEST = os.path.join(ROOT, 'dotnet_bindings', 'manifest.json')

with open(MANIFEST,'r',encoding='utf-8') as fh:
    manifest = json.load(fh)

# collect generated content for fast search
gen_files = {}
for fn in os.listdir(GENERATED_DIR):
    if fn.endswith('.cs'):
        with open(os.path.join(GENERATED_DIR,fn),'r',encoding='utf-8') as fh:
            gen_files[fn] = fh.read()

missing = []
issues = []

proto_re = re.compile(r"public static extern\s+([A-Za-z0-9_<>\?]+)\s+([A-Za-z0-9_]+)\s*\(([^)]*)\)")

for header, funcs in manifest.items():
    for f in funcs:
        name = f['name']
        found = False
        for fname, content in gen_files.items():
            if name in content:
                # look for the DllImport signature matching the function
                for m in proto_re.finditer(content):
                    ret, fname_m, params = m.groups()
                    if fname_m == name:
                        found = True
                        # check pointer-like args in manifest
                        args = [a.strip() for a in (f['args'] or '').split(',') if a.strip()]
                        for idx,a in enumerate(args):
                            # if arg contains '*' and not char*, analyze expectation
                            if '*' in a and 'char' not in a:
                                # find corresponding param in params
                                param_list = [p.strip() for p in params.split(',') if p.strip()]
                                if idx < len(param_list):
                                    p = param_list[idx]
                                    # param type is first token (may include ? or ref/out)
                                    p_tokens = p.split()
                                    ptype = p_tokens[0]

                                    # heuristic: primitive pointers (int*, double*, float*, long*, size_t*, etc.)
                                    if re.search(r"\b(int|double|float|long|size_t|uint32_t|unsigned|int32_t|uint32_t)\s*\*", a):
                                        # primitive out params should be 'out'/'ref' or IntPtr
                                        if not (('out' in p_tokens) or ('ref' in p_tokens) or (ptype == 'IntPtr') or (ptype == 'nint') or (ptype == 'nuint')):
                                            issues.append((name, header, f['args'], 'Expected out/ref/IntPtr for primitive pointer arg', p))
                                    else:
                                        # non-primitive pointer: expect SafeHandle
                                        if not re.match(r"Safe[A-Za-z0-9_]+\??", ptype):
                                            issues.append((name, header, f['args'], 'Expected SafeHandle for opaque pointer', p))
                                else:
                                    issues.append((name, header, f['args'], 'Param count mismatch in generated signature', params))
                        # check return type mapping for pointer returns
                        ret = f['ret'] or ''
                        if '*' in ret:
                            # returned char* -> string?
                            if 'char' in ret:
                                # expect string return
                                # find return types in the file
                                for m2 in proto_re.finditer(content):
                                    ret_m, name_m, params_m = m2.groups()
                                    if name_m == name:
                                        if not re.match(r"string\??", ret_m):
                                            issues.append((name, header, f['ret'], 'Expected string return for char*', ret_m))
                                        break
                            else:
                                # expect SafeHandle return
                                for m2 in proto_re.finditer(content):
                                    ret_m, name_m, params_m = m2.groups()
                                    if name_m == name:
                                        if not re.match(r"Safe[A-Za-z0-9_]+\??", ret_m):
                                            issues.append((name, header, f['ret'], 'Expected SafeHandle return for pointer return', ret_m))
                                        break
                        break
                if found:
                    break
        if not found:
            missing.append((name, header))

# Report
print('Total functions in manifest:', sum(len(v) for v in manifest.values()))
print('Missing in generated files:', len(missing))
if missing:
    for m in missing[:20]:
        print(' -',m)
print('\nPotential signature issues (pointer args not mapped to SafeHandle):', len(issues))
if issues:
    for it in issues[:40]:
        print(' -', it)

# exit code indicates errors
if missing or issues:
    exit(1)
else:
    print('All functions found and pointer args mapped to SafeHandles where expected.')
