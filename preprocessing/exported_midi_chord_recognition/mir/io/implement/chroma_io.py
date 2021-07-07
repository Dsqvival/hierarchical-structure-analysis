from mir.io.feature_io_base import *
import numpy as np

class ChromaIO(FeatureIO):
    def read(self, filename, entry):
        if(filename.endswith('.csv')):
            f=open(filename,'r')
            lines=f.readlines()
            result=[]
            for line in lines:
                line=line.strip()
                if(line==''):
                    continue
                arr=np.array(list(map(float,line.split(',')[2:])))
                arr=arr.reshape((2,12))[::-1].T
                arr=np.roll(arr,-3,axis=0).reshape((24))
                result.append(arr)
            data=np.array(result)
        else:
            data=pickle_read(self, filename)
        return data

    def write(self, data, filename, entry):
        pickle_write(self, data, filename)

    def visualize(self, data, filename, entry, override_sr):
        sr=entry.prop.sr
        win_shift=entry.prop.hop_length
        feature_tuple_size=entry.prop.chroma_tuple_size
        # if(FEATURETUPLESIZE==2):
        features=data
        f = open(filename, 'w')
        for i in range(0, features.shape[0]):
            time = win_shift * i / sr
            f.write(str(time))
            for j in range(0,feature_tuple_size):
                if(j>0):
                    f.write('\t0')
                for k in range(0, 12):
                    f.write('\t' + str(features[i][k*feature_tuple_size+j]))
            f.write('\n')
        f.close()

    def pre_assign(self, entry, proxy):
        entry.prop.set('n_frame', LoadingPlaceholder(proxy, entry))

    def post_load(self, data, entry):
        entry.prop.set('n_frame', data.shape[0])