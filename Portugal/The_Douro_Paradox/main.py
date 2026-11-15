import csv,json,hashlib  # Importă csv, json, hashlib
from pathlib import Path  # Importă Path din pathlib
from collections import defaultdict  # Importă defaultdict din collections

def counts(rows):  # Numără succesele și totalurile separat pentru control și tratament.
 v=[0,0,0,0]  # Stabilește v: vectorul [succese control, total control, succese tratament, total tratament].
 for r in rows:  # Parcurge rows; elementul curent este r.
  i=2*(r['treatment']=='treatment');v[i]+=int(r['harvest_success']);v[i+1]+=1  # Stabilește i: offsetul 0 pentru control sau 2 pentru tratament. Actualizează v[i] folosind int(r['harvest_success']). Actualizează v[i + 1] folosind 1.
 return v  # Întoarce v.

def reversal(v):  # Verifică dacă rata controlului depășește strict rata tratamentului.
 return v[1]>0 and v[3]>0 and v[0]*v[3]>v[2]*v[1]  # Cere ambele brațe nenule și compară exact ratele prin produse încrucișate: control > tratament.

def rates(v):  # Transformă contoarele în succese, totaluri și rate pe braț.
 return {a:{'successes':v[i],'plots':v[i+1],'rate':v[i]/v[i+1]} for a,i in [('control',0),('treatment',2)]}  # Formează pentru fiecare braț numărul succeselor, totalul parcelelor și raportul lor.

def screen(rows):  # Caută coloane și praguri care produc paradoxul Simpson.
 results=[]  # Inițializează raportul căutării pentru fiecare coloană eligibilă.
 for column in rows[0]:  # Parcurge rows[0]; elementul curent este column.
  if column in ['plot_id','treatment','harvest_success']:continue  # Execută ramura dacă column in ['plot_id', 'treatment', 'harvest_success']. Trece la următoarea iterație, ignorând restul blocului curent.
  try:values={r[column]:float(r[column]) for r in rows};numeric=True  # Încearcă interpretarea întregii coloane ca numere; dacă reușește, activează căutarea de praguri.
  except ValueError:values={r[column]:r[column] for r in rows};numeric=False  # La o valoare nenumerică, păstrează valorile drept categorii și dezactivează căutarea numerică.
  groups=defaultdict(lambda:[0,0,0,0])  # Stabilește groups: contoarele/grupurile separate după variabila analizată.
  for r in rows:  # Parcurge rows; elementul curent este r.
   v=groups[values[r[column]]];i=2*(r['treatment']=='treatment');v[i]+=int(r['harvest_success']);v[i+1]+=1  # Stabilește v: vectorul [succese control, total control, succese tratament, total tratament]. Stabilește i: offsetul 0 pentru control sau 2 pentru tratament. Actualizează v[i] folosind int(r['harvest_success']). Actualizează v[i + 1] folosind 1.
  if numeric:  # Execută ramura dacă numeric.
   total=counts(rows);left=[0,0,0,0];cuts=[]  # Stabilește total: contoarele întregului set. Stabilește left: contoarele valorilor ≤ pragul curent. Stabilește cuts: pragurile care inversează strict comparația în ambele grupuri.
   for value in sorted(groups)[:-1]:  # Parcurge sorted(groups)[:-1]; elementul curent este value.
    left=[a+b for a,b in zip(left,groups[value])];right=[a-b for a,b in zip(total,left)]  # Stabilește left: contoarele valorilor ≤ pragul curent. Stabilește right: contoarele valorilor > pragul curent.
    if reversal(left) and reversal(right):cuts.append(value)  # Execută ramura dacă reversal(left) and reversal(right). Adaugă elementul la sfârșitul colecției.
   results.append({'column':column,'kind':'numeric','levels':len(groups),'reversing_thresholds':cuts,'complete_reversal':bool(cuts)})  # Adaugă elementul la sfârșitul colecției.
  else:results.append({'column':column,'kind':'categorical','levels':len(groups),'complete_reversal':all(reversal(v) for v in groups.values())})  # Adaugă elementul la sfârșitul colecției.
 return results  # Întoarce results.

def main():  # Execută fluxul principal al soluției descris în DOCUMENTATION.md.
 path=Path('douro_vineyard_data.csv')  # Stabilește calea CSV-ului verificat de download.py.
 with path.open(encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))  # Citește rândurile CSV ca dicționare și închide automat fișierul.
 assert len(rows)==3543 and len({r['plot_id'] for r in rows})==len(rows)  # Oprește execuția dacă nu este adevărat: len(rows) == 3543 and len({r['plot_id'] for r in rows}) == len(rows).
 assert all(r['treatment'] in ['control','treatment'] and r['harvest_success'] in ['0','1'] and all(r.values()) for r in rows)  # Verifică tratamentele admise, rezultate binare și lipsa câmpurilor goale pentru toate parcelele.
 overall=counts(rows);assert overall[2]*overall[1]>overall[0]*overall[3]  # Stabilește overall: contoarele agregate pe toate parcelele. Oprește execuția dacă nu este adevărat: overall[2] * overall[1] > overall[0] * overall[3].
 scanned=screen(rows);found=[r for r in scanned if r['complete_reversal']]  # Stabilește scanned: rezultatele căutării pentru toate coloanele eligibile. Stabilește found: variabilele care produc inversarea completă.
 assert len(found)==1 and found[0]['kind']=='numeric'  # Oprește execuția dacă nu este adevărat: len(found) == 1 and found[0]['kind'] == 'numeric'.
 column=found[0]['column'];cut=max(found[0]['reversing_thresholds'])  # Stabilește column: unica variabilă numerică identificată. Stabilește cut: cel mai mare prag observat care păstrează inversarea în ambele grupuri.
 groups={label:[r for r in rows if (float(r[column])<=cut)==side] for label,side in [(f'<= {cut:g} km',True),(f'> {cut:g} km',False)]}  # Stabilește groups: contoarele/grupurile separate după variabila analizată.
 assert sum(map(len,groups.values()))==len(rows) and all(reversal(counts(g)) for g in groups.values())  # Oprește execuția dacă nu este adevărat: sum(map(len, groups.values())) == len(rows) and all((reversal(counts(g)) for g in groups.values())).
 flag='SIGMOID_'+column.upper()  # Stabilește flag: prefixul SIGMOID_ urmat de numele coloanei cu majuscule.
 result={'flag':flag,'column':column,'threshold':cut,'rows':len(rows),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'overall':rates(overall),'groups':{k:rates(counts(g)) for k,g in groups.items()},'screening':scanned,'threshold_selection':'largest observed numeric boundary producing a strict reversal in both groups'}  # Reunește flagul, pragul, hashul datelor, ratele și toate rezultatele screeningului într-un raport.
 easier=max(result['groups'],key=lambda k:sum(v['successes'] for v in result['groups'][k].values())/sum(v['plots'] for v in result['groups'][k].values()))  # Stabilește easier: grupul cu rata combinată de succes mai mare.
 weights={a:result['groups'][easier][a]['plots']/result['overall'][a]['plots'] for a in ['control','treatment']}  # Stabilește weights: ponderea parcelelor fiecărui braț în grupul cu succes mai mare.
 result['pooling_explanation']=f"Treatment has {weights['treatment']:.2%} of its plots in the higher-success {easier} group, versus {weights['control']:.2%} for control; pooling these differently weighted groups puts treatment ahead despite its lower success rate within both groups."  # Explică inversarea agregată prin ponderile diferite ale brațelor în grupul cu succes mai mare.
 Path('result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')  # Scrie textul în fișierul indicat.
 Path('flag.txt').write_text(flag+'\n',encoding='utf-8')  # Scrie textul în fișierul indicat.
 with open('rates.csv','w',encoding='utf-8',newline='') as f:  # Gestionează automat contextul: open('rates.csv', 'w', encoding='utf-8', newline='').
  w=csv.writer(f);w.writerow(['group','treatment','successes','plots','success_rate'])  # Creează scriitorul CSV și scrie antetul raportului de rate.
  for label,table in [('Overall',result['overall']),*result['groups'].items()]:  # Parcurge [('Overall', result['overall']), *result['groups'].items()]; elementul curent este (label, table).
   for arm,v in table.items():w.writerow([label,arm,v['successes'],v['plots'],v['rate']])  # Scrie câte un rând CSV cu grupul, brațul, succesele, totalul și rata sa.
 print(flag)  # Afișează valorile sau mesajul pentru verificare.
 print(json.dumps({k:result[k] for k in ['overall','groups']},indent=2))  # Afișează valorile sau mesajul pentru verificare.

if __name__=='__main__':main()  # Pornește execuția numai când fișierul este rulat direct. Apelează main.
