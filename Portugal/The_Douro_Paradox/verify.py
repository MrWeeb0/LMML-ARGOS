import csv,json  # Importă csv, json
from pathlib import Path  # Importă Path din pathlib
from fractions import Fraction  # Importă Fraction din fractions

def main():  # Execută fluxul principal al soluției descris în DOCUMENTATION.md.
 result=json.loads(Path('result.json').read_text())  # Încarcă rezultatul salvat de main.py pentru verificare independentă.
 with open('douro_vineyard_data.csv',encoding='utf-8-sig',newline='') as f:rows=list(csv.DictReader(f))  # Recitește datele brute, fără a reutiliza contoarele calculate de solver.
 key=result['column'];cut=result['threshold'];cells={}  # Recuperează variabila și pragul din raport; pregătește tabelul verificărilor exacte.
 for label,subset in [('Overall',rows),(f'<= {cut:g} km',[r for r in rows if float(r[key])<=cut]),(f'> {cut:g} km',[r for r in rows if float(r[key])>cut])]:  # Verifică separat întregul set, grupul ≤ prag și grupul > prag.
  arms={a:[int(r['harvest_success']) for r in subset if r['treatment']==a] for a in ['control','treatment']}  # Separă rezultatele binare pe braț în grupul curent.
  rates={a:Fraction(sum(v),len(v)) for a,v in arms.items()}  # Stabilește rates: ratele exacte sub formă de fracții, fără rotunjire binară.
  assert rates['treatment']>rates['control'] if label=='Overall' else rates['control']>rates['treatment']  # Oprește execuția dacă nu este adevărat: rates['treatment'] > rates['control'] if label == 'Overall' else rates['control'] > rates['treatment'].
  saved=result['overall'] if label=='Overall' else result['groups'][label]  # Selectează contoarele salvate corespunzătoare grupului verificat.
  for a,v in arms.items():assert saved[a]['successes']==sum(v) and saved[a]['plots']==len(v)  # Parcurge arms.items(); elementul curent este (a, v). Oprește execuția dacă nu este adevărat: saved[a]['successes'] == sum(v) and saved[a]['plots'] == len(v).
  cells[label]={a:{'fraction':str(rate),'percent':float(rate)*100} for a,rate in rates.items()}  # Înregistrează ratele exacte ca fracții și procente pentru raportul verificării.
 for a in ['control','treatment']:  # Parcurge ['control', 'treatment']; elementul curent este a.
  for field in ['successes','plots']:assert sum(t[a][field] for t in result['groups'].values())==result['overall'][a][field]  # Parcurge ['successes', 'plots']; elementul curent este field. Oprește execuția dacă nu este adevărat: sum((t[a][field] for t in result['groups'].values())) == result['overall'][a][field].
 check={'passed':True,'rows':len(rows),'complete_partition':sum(t[a]['plots'] for t in result['groups'].values() for a in t)==len(rows),'exact_rates':cells}  # Stabilește check: raportul verificării independente a ratelor și partiției.
 assert check['complete_partition']  # Oprește execuția dacă nu este adevărat: check['complete_partition'].
 Path('verification.json').write_text(json.dumps(check,indent=2)+'\n',encoding='utf-8')  # Scrie textul în fișierul indicat.
 print('Exact-fraction verification passed')  # Afișează valorile sau mesajul pentru verificare.

if __name__=='__main__':main()  # Pornește execuția numai când fișierul este rulat direct. Apelează main.
