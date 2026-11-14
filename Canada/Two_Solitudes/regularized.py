import csv
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.linear_model import LogisticRegression
from featurize import featurize
from open_vault import CLASSES

r=list(csv.DictReader(open('corpus.csv',encoding='utf-8')))
X=csr_matrix(featurize([v['text'] for v in r]))
y=[CLASSES.index(v['label']) for v in r]
m=LogisticRegression(C=1,max_iter=3000).fit(X,y)
W=np.zeros((9,4096))
b=np.zeros(9)
W[m.classes_],b[m.classes_]=m.coef_,m.intercept_
np.savez('regularized_model.npz',W=W,b=b)
