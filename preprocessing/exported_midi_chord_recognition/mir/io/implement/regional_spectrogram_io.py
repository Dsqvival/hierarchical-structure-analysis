from mir.io.feature_io_base import *
from mir.common import PACKAGE_PATH
import numpy as np

class RegionalSpectrogramIO(FeatureIO):
    def read(self, filename, entry):
        data=pickle_read(self, filename)
        assert(len(data)==3 or len(data)==2)
        return data

    def write(self, data, filename, entry):
        assert(len(data)==3 or len(data)==2)
        pickle_write(self, data, filename)

    def visualize(self, data, filename, entry, override_sr):
        if(len(data)==2):
            timing,data=data
            labels=None
        elif(len(data)==3):
            labels,timing,data=data
        else:
            raise Exception("Format error")
        data=np.array(data)
        if(len(data.shape)==1):
            data=data.reshape((-1,1))
        sr = entry.prop.sr
        win_shift=entry.prop.hop_length
        timing=np.array(timing).reshape((len(timing),-1))
        n_frame=max(1,int(np.round(np.max(timing*sr/win_shift))))
        data_indices=(-1)*np.ones(n_frame,dtype=np.int32)
        timing_start=timing[:len(data),0]
        if(timing.shape[1]==1):
            assert(len(timing)==len(data) or len(timing)==len(data)+1)
            if(len(timing)==len(data)+1):
                timing_end=timing[1:,0]
            else:
                timing_end=np.append(timing[1:,0],timing[-1,0]*2-timing[-2,0] if(len(timing)>1) else 1.0)
        else:
            timing_end=timing[:,1]
        for i in range(len(data)):
            frame_start=max(0,int(np.round(timing_start[i]*sr/win_shift)))
            frame_end=max(0,int(np.round(timing_end[i]*sr/win_shift)))
            data_indices[frame_start:frame_end]=i
        if(data.shape[1]>=1):
            f = open(os.path.join(PACKAGE_PATH,'data/spectrogram_template.svl'), 'r')
            content = f.read()
            f.close()
            content = content.replace('[__SR__]', str(sr))
            content = content.replace('[__WIN_SHIFT__]', str(win_shift))
            content = content.replace('[__SHAPE_1__]', str(data.shape[1]))
            content = content.replace('[__COLOR__]', str(1))
            if(labels is None):
                labels = [str(i) for i in range(data.shape[1])]
            assert(len(labels)==len(data[0]))
            result='\n'.join(['<bin number="%d" name="%s"/>' % (i, str(labels[i])) for i in range(len(labels))])+'\n'
            for i in range(n_frame):
                if(data_indices[i]>=0):
                    result +='<row n="%d">%s</row>\n' % (i, ' '.join([
                        str(s) for s in data[data_indices[i]]
                    ]))
            content = content.replace('[__DATA__]',result)
        else:
            f = open(os.path.join(PACKAGE_PATH,'data/curve_template.svl'), 'r')
            content = f.read()
            f.close()
            content = content.replace('[__SR__]', str(sr))
            content = content.replace('[__STYLE__]', str(1))
            results=[]
            raise NotImplementedError()
            # for i in range(0, len(data)):
            #     results.append('<point frame="%d" value="%f" label="" />'%(int(override_sr/sr*i*win_shift),data[i,0]))
            # content = content.replace('[__DATA__]','\n'.join(results))
            # content = content.replace('[__NAME__]', 'curve')

        f=open(filename,'w')
        f.write(content)
        f.close()

    def get_visualize_extention_name(self):
        return "svl"