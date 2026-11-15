from pathlib import Path
import numpy as np
from scipy.io import wavfile
from scipy.signal import welch,find_peaks,iirnotch,tf2sos,sosfiltfilt,stft,istft
from scipy.ndimage import median_filter,gaussian_filter
HERE=Path(__file__).resolve().parent
sr,raw=wavfile.read(HERE/'voice_note.wav');x=raw.astype(np.float32)/32768
f,p=welch(x,fs=sr,nperseg=65536)
bg=median_filter(10*np.log10(p+1e-20),size=301)
peaks,_=find_peaks(10*np.log10(p+1e-20)-bg,prominence=10,distance=30)
peaks=peaks[(f[peaks]>100)&(f[peaks]<5000)&(10*np.log10(p[peaks])-bg[peaks]>12)]
print('notches',f[peaks],flush=True)
sos=np.concatenate([tf2sos(*iirnotch(float(hz),float(hz)/12,fs=sr)) for hz in f[peaks]])
y=sosfiltfilt(sos,x).astype(np.float32)
np.save(HERE/'notched.npy',y)
def save(name,a):
 gain=min(.9/(np.quantile(abs(a),.9999)+1e-9),25)
 wavfile.write(HERE/name,sr,np.clip(a*gain*32767,-32768,32767).astype(np.int16))
save('notched.wav',y)
for nfft in [1024,4096]:
 f,t,z=stft(y,fs=sr,nperseg=nfft,noverlap=nfft*3//4)
 power=abs(z)**2
 noise=np.quantile(power,.35,axis=1,keepdims=True)
 gain=np.maximum(1-2*noise/(power+1e-20),.015)**.8
 gain=gaussian_filter(gain,sigma=(.5,1))
 _,a=istft(z*gain,fs=sr,nperseg=nfft,noverlap=nfft*3//4)
 save(f'clean_{nfft}.wav',a[:len(x)])
 print('saved',nfft,flush=True)
