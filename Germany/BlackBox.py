import itertools  # Importă itertools
import numpy as np  # Importă numpy ca np


def solve(oracle, points):  # Identifică modelul oracolului și prezice punctele cerute.
    pairs = list(itertools.combinations(range(5), 2))  # Stabilește pairs: cele zece perechi posibile dintre cinci variabile.
    names = ['x%d' % (i + 1) for i in range(5)]  # Stabilește names: numele x1 până la x5.
    X, Y = [], []  # Inițializează istoricul punctelor interogate și al răspunsurilor primite.

    def ask(p, phase):  # Interoghează oracolul și înregistrează punctul și răspunsul.
        p = [float(v) for v in p]  # Convertește coordonatele în float înainte de apelul oracolului.
        y = float(oracle.ask(p, phase=phase))  # Consumă o interogare din buget și convertește răspunsul la float.
        X.append(p)  # Adaugă elementul la sfârșitul colecției.
        Y.append(y)  # Adaugă elementul la sfârșitul colecției.
        return y  # Întoarce y.

    def features(x):  # Construiește constanta, termenii centrați și produsele perechi.
        z = np.asarray(x, dtype=float) - .5  # Centrează cele cinci coordonate în jurul lui 0,5.
        return np.column_stack([np.ones(len(z)), z,  # Întoarce np.column_stack([np.ones(len(z)), z, *[z[:, i] * z[:, j] for i, j in pairs]]).
                                *[z[:, i]*z[:, j] for i, j in pairs]])  # Adaugă cele zece produse între perechi de coordonate centrate.

    # Walsh contrasts on a full local factorial reveal effects invisible
    # on the five coordinate axes. A second, global factorial finds gates.
    signs = np.array(list(itertools.product([-1., 1.], repeat=5)))  # Stabilește signs: cele 32 de combinații factoriale ale semnelor.
    local = .5 + .125*signs  # Stabilește local: punctele factoriale locale, la 0,375 și 0,625.
    yl = np.array([ask(p, 'local factorial') for p in local])  # Stabilește yl: răspunsurile oracolului la experimentul local.
    beta = np.linalg.lstsq(features(local), yl, rcond=None)[0]  # Stabilește beta: coeficienții termenului constant, celor cinci efecte și celor zece produse.
    corners = (signs + 1)/2  # Stabilește corners: cele 32 de colțuri ale cubului [0, 1]^5.
    yc = np.array([ask(p, 'global factorial') for p in corners])  # Stabilește yc: răspunsurile oracolului la colțurile cubului.
    A = features(X)  # Construiește matricea celor 16 termeni pentru toate punctele interogate până aici.
    y = np.array(Y)  # Construiește un tablou NumPy; rezultatul este păstrat în y.

    # If a switching surface crossed the local experiment, use consensus
    # fitting within the documented one-product family instead.
    if (np.max(np.abs(features(local) @ beta - yl)) > 1e-5 or  # Declanșează recuperarea prin consens și când modelul nu are exact un produs semnificativ.
            np.sum(np.abs(beta[6:]) > 1e-3) != 1):  # Cere exact un produs pereche cu coeficient absolut peste 0,001.
        rng = np.random.default_rng(9137)  # Fixează seed-ul căutării prin consens pentru reproductibilitate.
        best = None  # Inițializează cel mai bun candidat; nu a fost încă găsit un model.
        for q in range(10):  # Parcurge range(10); elementul curent este q.
            cols = list(range(6)) + [6+q]  # Păstrează constanta, cei cinci termeni liniari și un singur produs candidat.
            B = A[:, cols]  # Extrage din matrice numai coloanele familiei de produs curente.
            for _ in range(180):  # Parcurge range(180); elementul curent este _.
                ix = rng.choice(len(y), 7, replace=False)  # Alege șapte ecuații distincte pentru cei șapte coeficienți ai candidatului.
                try:  # Încearcă operația; ramura except tratează eroarea prevăzută.
                    b = np.linalg.solve(B[ix], y[ix])  # Rezolvă exact sistemul de șapte ecuații; un sistem singular este ignorat.
                except np.linalg.LinAlgError:  # Tratează np.linalg.LinAlgError prin ramura alternativă.
                    continue  # Trece la următoarea iterație, ignorând restul blocului curent.
                r = np.abs(B @ b-y)  # Calculează erorile absolute ale modelului candidat pe toate probele.
                good = r < 2e-5  # Consideră consens punctele cu eroare sub 0,00002.
                key = (int(good.sum()), -float(np.minimum(r, 1).sum()))  # Preferă mai multe puncte de consens, apoi eroare trunchiată totală mai mică.
                if best is None or key > best[0]:  # Execută ramura dacă best is None or key > best[0].
                    best = (key, cols, good, b)  # Memorează scorul, familia, masca de consens și coeficienții celui mai bun candidat.
        _, cols, good, b = best  # Recuperează configurația câștigătoare a căutării prin consens.
        beta = np.zeros(16)  # Stabilește beta: coeficienții termenului constant, celor cinci efecte și celor zece produse.
        beta[cols] = np.linalg.lstsq(A[good][:, cols], y[good], rcond=None)[0]  # Reajustează coeficienții familiei câștigătoare folosind numai punctele de consens.

    # Residuals are two constant levels. Use the lower level as the
    # reference, so the recovered jump and active halfspace are positive.
    residual = yc - features(corners) @ beta  # Stabilește residual: răspunsurile globale minus componenta netedă estimată.
    low, high = float(np.min(residual)), float(np.max(residual))  # Identifică nivelul minim și maxim al reziduurilor la colțuri.
    labels = residual > (low+high)/2  # Stabilește labels: nivelul rezidual superior, care indică activarea saltului.
    beta[0] += float(np.median(residual[~labels]))  # Actualizează beta[0] folosind float(np.median(residual[~labels])).
    jump = float(np.median(residual[labels])-np.median(residual[~labels])) if labels.any() else 0.  # Stabilește jump: amplitudinea estimată a saltului.
    edges = []  # Pregătește lista muchiilor pe care saltul își schimbă starea.
    gate = set()  # Stabilește gate: indicii variabilelor implicate în poarta discontinuității.
    for a in range(32):  # Parcurge range(32); elementul curent este a.
        for j in range(5):  # Parcurge range(5); elementul curent este j.
            b = a ^ (1 << (4-j))  # Inversează un singur bit al indicelui pentru a găsi colțul vecin pe axa j.
            if a < b and labels[a] != labels[b]:  # Reține o muchie o singură dată și numai dacă saltul diferă la capete.
                edges.append((a, b))  # Adaugă elementul la sfârșitul colecției.
                gate.add(j)  # Include elementul în mulțime.
    gate = sorted(gate)  # Stabilește gate: indicii variabilelor implicate în poarta discontinuității.
    normal = np.zeros(5)  # Stabilește normal: normala unitară a frontierei, în cinci dimensiuni.
    threshold = 0.  # Inițializează cu zero normala frontierei; va fi estimată dacă există poartă.
    cuts = []  # Inițializează pragul frontierei înainte de estimare.

    if gate:  # Execută ramura dacă gate.
        # Select affinely independent crossings in the gate subspace.
        candidates = list(edges)  # Copiază muchiile candidate pentru selectarea traversărilor diverse.
        chosen = []  # Inițializează lista traversărilor alese.
        target = min(len(edges), len(gate)+2)  # Limitează numărul traversărilor la numărul variabilelor porții plus două.
        while candidates and len(chosen) < target:  # Repetă blocul cât timp candidates and len(chosen) < target.
            def diversity(e):  # Măsoară câtă informație geometrică nouă aduce muchia candidat.
                p = (corners[e[0], gate]+corners[e[1], gate])/2  # Calculează mijlocul muchiei în subspațiul variabilelor porții.
                v = np.append(p, 1.)  # Adaugă coordonata omogenă 1 pentru testarea independenței afine.
                if not chosen:  # Execută ramura dacă not chosen.
                    return 1.  # Întoarce 1.0.
                M = np.array([np.append((corners[a, gate]+corners[b, gate])/2, 1.) for a,b in chosen])  # Construiește matricea mijloacelor traversărilor deja alese, în coordonate omogene.
                r = v - np.linalg.lstsq(M.T, v, rcond=None)[0] @ M  # Scade proiecția candidatului pe spațiul traversărilor existente; restul măsoară informația nouă.
                return float(r @ r)  # Întoarce float(r @ r).
            e = max(candidates, key=diversity)  # Alege traversarea cu cel mai mare rest geometric față de cele existente.
            chosen.append(e)  # Adaugă elementul la sfârșitul colecției.
            candidates.remove(e)  # Elimină muchia aleasă din lista candidaților pentru a nu o selecta din nou.
        iterations = min(14, max(7, (int(oracle.remaining)-12)//len(chosen)))  # Stabilește iterations: numărul de bisecții adaptat bugetului rămas.
        for a, b in chosen:  # Parcurge chosen; elementul curent este (a, b).
            left, right = corners[a].copy(), corners[b].copy()  # Copiază cele două capete ale muchiei pentru căutarea binară.
            lab = bool(labels[a])  # Memorează starea saltului de la capătul stâng.
            for _ in range(iterations):  # Parcurge range(iterations); elementul curent este _.
                if oracle.remaining <= 10:  # Execută ramura dacă oracle.remaining <= 10.
                    break  # Încheie bucla curentă.
                p = (left+right)/2  # Înjumătățește intervalul de pe muchia care traversează frontiera.
                val = ask(p, 'boundary bisection')  # Interoghează funcția la mijlocul intervalului, contabilizând proba.
                r = val - float(features([p])[0] @ beta)  # Scade partea netedă pentru a decide pe ce nivel al saltului se află mijlocul.
                if (r > jump/2) == lab:  # Execută ramura dacă (r > jump / 2) == lab.
                    left = p  # Mută capătul stâng dacă mijlocul are aceeași stare a saltului.
                else:  # Traitează cazul în care condiția precedentă este falsă.
                    right = p  # Mută capătul drept dacă mijlocul are starea opusă.
            cuts.append((left+right)/2)  # Adaugă elementul la sfârșitul colecției.
        M = np.column_stack([np.array(cuts)[:, gate], -np.ones(len(cuts))])  # Construiește matricea concatenând coloanele; rezultatul este păstrat în M.
        _, _, vt = np.linalg.svd(M, full_matrices=True)  # Calculează vectorii singulari drepți ai ecuațiilor frontierei.
        plane = vt[-1]  # Selectează vectorul singular care aproximează cel mai bine nucleul matricei.
        n, t = plane[:-1], float(plane[-1])  # Separă normala și pragul din coeficienții omogeni ai planului.
        if np.mean(corners[labels][:, gate] @ n-t) < 0:  # Execută ramura dacă np.mean(corners[labels][:, gate] @ n - t) < 0.
            n, t = -n, -t  # Inversează simultan normala și pragul pentru orientarea către saltul pozitiv.
        scale = np.linalg.norm(n)  # Calculează norma euclidiană pentru normalizarea ecuației planului.
        normal[gate] = n/scale  # Inserează normala unitară în coordonatele relevante ale spațiului cu cinci dimensiuni.
        threshold = float(t/scale)  # Stabilește threshold: pragul planului care activează saltul.

    # Independent probes test the full model, then refine its coefficients
    # away from the estimated switching surface.
    rng = np.random.default_rng(7619)  # Fixează un seed separat pentru probele suplimentare.
    for _ in range(min(10, int(oracle.remaining))):  # Parcurge range(min(10, int(oracle.remaining))); elementul curent este _.
        ask(rng.uniform(0, 1, 5), 'independent verification')  # Sondează un punct aleator uniform din cub și îl adaugă istoricului de ajustare.
    xx = np.array(X)  # Construiește un tablou NumPy; rezultatul este păstrat în xx.
    yy = np.array(Y)  # Construiește un tablou NumPy; rezultatul este păstrat în yy.
    q = int(np.argmax(np.abs(beta[6:])))  # Identifică produsul cu cel mai mare coeficient absolut.
    cols = list(range(6)) + [6+q]  # Selectează constanta, cei cinci termeni liniari și produsul identificat.
    active = (xx @ normal >= threshold).astype(float) if gate else np.zeros(len(xx))  # Indică pentru fiecare probă dacă se află în semispațiul cu salt activ.
    safe = np.abs(xx @ normal-threshold) > .002 if gate else np.ones(len(xx), dtype=bool)  # Stabilește safe: masca punctelor aflate la peste 0,002 de frontiera estimată.
    B = np.column_stack([features(xx)[:, cols], active])  # Construiește matricea concatenând coloanele; rezultatul este păstrat în B.
    b = np.linalg.lstsq(B[safe], yy[safe], rcond=None)[0]  # Reajustează cei șapte termeni netezi și saltul pe punctele departe de frontieră.
    beta[:] = 0.  # Resetează toți coeficienții înainte de inserarea ajustării finale.
    beta[cols] = b[:-1]  # Inserează coeficienții netezi în coloanele modelului complet.
    jump = float(b[-1])  # Stabilește jump: amplitudinea estimată a saltului.
    i, j = pairs[q]  # Recuperează indicii celor două variabile din produsul selectat.
    coefficient = float(beta[6+q])  # Extrage coeficientul produsului pentru raportare.
    relevant = {k for k in range(5) if abs(beta[1+k]) > 1e-4}  # Stabilește relevant: variabilele cu efect liniar, produs sau rol în poartă.
    if abs(coefficient) > 1e-4:  # Execută ramura dacă abs(coefficient) > 0.0001.
        relevant.update((i, j))  # Actualizează contorul sau colecția cu elementele indicate.
    relevant.update(gate)  # Actualizează contorul sau colecția cu elementele indicate.
    terms = [repr(float(beta[0]))]  # Începe expresia textuală a modelului cu termenul constant.
    terms += ['(%r)*(x%d-0.5)' % (float(beta[1+k]), k+1) for k in range(5) if abs(beta[1+k]) > 1e-9]  # Actualizează terms folosind ['(%r)*(x%d-0.5)' % (float(beta[1 + k]), k + 1) for k in range(5) if abs(beta[1 + k]) > 1e-09].
    terms.append('(%r)*(x%d-0.5)*(x%d-0.5)' % (coefficient, i+1, j+1))  # Adaugă elementul la sfârșitul colecției.
    condition = ' + '.join('(%r)*x%d' % (float(normal[k]), k+1) for k in gate) or '0'  # Stabilește condition: condiția textuală de activare a saltului.
    condition += ' >= %r' % threshold  # Actualizează condition: condiția textuală de activare a saltului.
    if gate:  # Execută ramura dacă gate.
        terms.append('(%r if %s else 0.0)' % (jump, condition))  # Adaugă elementul la sfârșitul colecției.
    xp = np.asarray(points, dtype=float)  # Convertește datele în tablou NumPy; rezultatul este păstrat în xp.
    predictions = features(xp) @ beta  # Stabilește predictions: predicțiile modelului pentru punctele evaluatorului.
    if gate:  # Execută ramura dacă gate.
        predictions += jump*(xp @ normal >= threshold)  # Actualizează predictions: predicțiile modelului pentru punctele evaluatorului.
    return {  # Întoarce raportul structurat cerut de evaluator: variabile, interacțiune, poartă, expresie și predicții.
        'relevant_variables': [names[k] for k in sorted(relevant)],  # Definește câmpul 'relevant_variables' al structurii curente.
        'irrelevant_variables': [names[k] for k in range(5) if k not in relevant],  # Definește câmpul 'irrelevant_variables' al structurii curente.
        'interactions': [{'variables': [names[i], names[j]], 'type': 'product',  # Definește câmpul 'interactions' al structurii curente.
                          'coefficient': coefficient}],  # Definește câmpul 'coefficient' al structurii curente.
        'discontinuities': [{'gate_variables': [names[k] for k in gate],  # Definește câmpul 'discontinuities' al structurii curente.
                             'boundary': {'form': 'linear', 'coefficients': dict(zip(names, map(float, normal))),  # Definește câmpul 'boundary' al structurii curente.
                                          'threshold': float(threshold), 'active_when': 'greater_equal'},  # Definește câmpul 'threshold' al structurii curente.
                             'jump': jump, 'condition': condition}] if gate else [],  # Definește câmpul 'jump' al structurii curente.
        'model_expression': ' + '.join(terms),  # Definește câmpul 'model_expression' al structurii curente.
        'predictions': predictions.tolist(),  # Definește câmpul 'predictions' al structurii curente.
        'notes': 'Local and global full factorials; residual-level gate detection; independent edge bisections; held-back verification probes. All coefficients inferred from oracle responses.'  # Definește câmpul 'notes' al structurii curente.
    }  # Închide dicționarul sau mulțimea.

