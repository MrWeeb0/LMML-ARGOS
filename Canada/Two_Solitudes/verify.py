import hashlib,json,platform
from pathlib import Path
import numpy as np
import scipy,sklearn
from open_vault import load_sealed,try_vault

X=load_sealed()
words={}
for name in ['first_model.npz','regularized_model.npz','model.npz']:
 if not Path(name).exists():continue
 z=np.load(name)
 assert set(z.files)=={'W','b'}
 assert z['W'].shape==(9,4096) and z['b'].shape==(9,)
 assert all(np.isfinite(z[k]).all() for k in z.files)
 words[name]=try_vault(X@z['W'].T+z['b'])
r=dict(status='platform_unverified',python=platform.python_version(),numpy=np.__version__,scikit_learn=sklearn.__version__,scipy=scipy.__version__,local_vault_words=words,sha256={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path('.').iterdir()) if p.is_file() and p.name!='verification.json'})
Path('verification.json').write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8')
print(json.dumps(r,indent=2))
