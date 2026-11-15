import csv,hashlib,json,os
from collections import Counter
from pathlib import Path
import numpy as np
from PIL import Image

root=Path(__file__).parent

def verify(folder):
    data=json.loads((folder/'detections.json').read_text())
    assert len(data)==130
    ids={(r['album'],r['page']) for r in data}
    assert len(ids)==130
    assert Counter(r['album'] for r in data)=={f'album_{i}':26 for i in range(1,6)}
    manifest=json.loads((root/'manifest.json').read_text())
    known={r['path'] for r in manifest}
    for r in data:
        assert f"albums/{r['album']}/{r['page']}.jpg" in known
        x,y,w,h=r['box'];cx,cy=r['center']
        assert 0<=x<x+w<=1600 and 0<=y<y+h<=1200
        assert x<=cx<=x+w and y<=cy<=y+h
        assert np.isfinite(r['score'])
        name=f"{r['album']}-{r['page']}"
        with np.load(folder/'heatmaps'/(name+'.npz')) as z:
            a=z['heat']
            assert a.shape==(300,400) and np.isfinite(a).all() and a.min()>=0 and a.max()<=1
        with Image.open(folder/'detections'/(name+'.jpg')) as im:
            assert im.size==(800,600)
    with (folder/'boxes.csv').open(newline='') as f:
        reader=csv.DictReader(f)
        assert reader.fieldnames==['album','page','x','y','w','h']
        boxes=list(reader)
    expected={(r['album'],r['page']):r['box'] for r in data}
    assert len(boxes)==130
    for r in boxes: assert [int(r[k]) for k in ['x','y','w','h']]==expected[(r['album'],r['page'])]
    assert len(list((folder/'heatmaps').glob('*.npz')))==130
    assert len(list((folder/'detections').glob('*.jpg')))==130
    with Image.open(folder/'album-overlays.png') as im:assert im.size==(2000,340)
    return {'pages':130,'unique_pages':130,'albums':5,'pages_per_album':26,'heatmaps':130,'annotated_images':130,'boxes_in_bounds':True,'csv_matches_detections':True}

results={name:verify(root/name) for name in ['pixel-output','synthetic-output']}
for name in ['pixel-detector.pt','pixel-synthetic-detector.pt']:
    assert (root/name).is_file()
    results[name]={'bytes':(root/name).stat().st_size,'sha256':hashlib.sha256((root/name).read_bytes()).hexdigest()}
for name in ['joint-letter-analysis.json','shared-geometry/results.json']:
    for item in json.loads((root/name).read_text()):assert item['verified_flag'] is None
report={'checked_commit':os.environ.get('GITHUB_SHA'),'status':'structural checks passed','flag_verified':False,'platform_pass_confirmed':False,'results':results}
(root/'material-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
