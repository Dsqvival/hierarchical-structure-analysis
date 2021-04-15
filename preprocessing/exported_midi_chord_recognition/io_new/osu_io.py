from mir.io.feature_io_base import *

class MetaDict:
    def __init__(self):
        self.dict={}

    def set(self,key,value):
        self.dict[key]=value

    def __getattr__(self, item):
        return self.dict[item.lower()]

class OsuMapIO(FeatureIO):
    def read(self, filename, entry):
        f=open(filename,'r',encoding='UTF-8')
        result=MetaDict()
        lines=f.readlines()
        current_state=0
        current_dict=None
        for line in lines:
            line=line.strip()
            if(line==''):
                continue
            if(line.startswith('[')):
                assert(line.endswith(']'))
                namespace=line[1:-1].lower()
                if(namespace in ['general','editor','metadata','difficulty','colours']):
                    current_state=1
                    current_dict=MetaDict()
                    result.set(namespace,current_dict)
                elif(namespace in ['hitobjects','events','timingpoints']):
                    current_state=2
                    current_dict=[]
                    result.set(namespace,current_dict)
                else:
                    raise Exception('Unknown namespace %s in %s'%(namespace,filename))
            else:
                if(current_state==1):
                    split_index=line.index(':')
                    key=line[:split_index].strip()
                    value=line[split_index+1:].strip()
                    current_dict.set(key.lower(),value)
                elif(current_state==2):
                    current_dict.append(line)
        return result

    def write(self, data, filename, entry):
        raise NotImplementedError()

    def visualize(self, data, filename, entry, override_sr):
        raise NotImplementedError()

    def get_visualize_extention_name(self):
        raise NotImplementedError()