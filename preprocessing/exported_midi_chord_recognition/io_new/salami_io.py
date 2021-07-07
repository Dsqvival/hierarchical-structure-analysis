from mir.io.feature_io_base import *
from mir.music_base import get_scale_and_suffix

class SalamiIO(FeatureIO):
    def read(self, filename, entry):
        f=open(filename,'r')
        data=f.read()
        lines=data.split('\n')
        result=[]
        metre_up=-1
        metre_down=-1
        tonic=-1
        for line in lines:
            if(line==''):
                continue
            if(line.startswith('#')):
                if(':' in line):
                    seperator_index=line.index(':')
                    keyword=line[1:seperator_index].strip()
                    if(keyword=='metre'):
                        slash_index=line.index('/')
                        metre_up=int(line[seperator_index+1:slash_index].strip())
                        metre_down=int(line[slash_index+1:].strip())
                        # print('metre changed to %d/%d'%(metre_up,metre_down))
                    if(keyword=='tonic'):
                        tonic=int(get_scale_and_suffix(line[seperator_index+1:].strip())[0])

            else:
                tokens=line.split('\t')
                assert(len(tokens)==2)
                start_time=float(tokens[0])
                result.append((start_time,tokens[1],metre_up,metre_down,tonic))
        f.close()
        return result

    def write(self, data, filename, entry):
        raise NotImplementedError()

    def visualize(self, data, filename, entry, override_sr):
        f=open(filename,'w')
        for (time,token,_,_,_) in data:
            f.write('%f\t%s\n'%(time,token))
        f.close()