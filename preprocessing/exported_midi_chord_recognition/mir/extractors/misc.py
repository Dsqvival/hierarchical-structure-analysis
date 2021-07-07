from mir.extractors.extractor_base import *
import librosa
import numpy as np

class BlankMusic(ExtractorBase):
    def get_feature_class(self):
        return io.MusicIO

    def extract(self,entry,**kwargs):
        time=60.0 # seconds
        if('time' in kwargs):
            time=kwargs['time']
        return np.zeros((int(np.ceil(time*entry.prop.sr))))


class FrameCount(ExtractorBase):
    def get_feature_class(self):
        return io.IntegerIO

    def extract(self,entry,**kwargs):
        # self.require(entry.prop.hop_length)
        return entry.dict[kwargs['source']].get(entry).shape[0]

class Evaluate():

    def __init__(self, io):
        self.__io=io

    def __call__(self, *args, **kwargs):
        inner_instance=Evaluate.InnerEvaluate()
        inner_instance.io=self.__io
        return inner_instance

    class InnerEvaluate(ExtractorBase):
        def __init__(self):
            self.io=None

        def get_feature_class(self):
            return self.io

        class __ProxyReflector():

            def __init__(self,entry):
                self.__entry=entry

            def __getattr__(self, item):
                if(item in self.__entry.dict):
                    print('Getting %s'%item)
                    return self.__entry.dict[item].get(self.__entry)
                else:
                    raise AttributeError('No key \'%s\' found in entry %s'%(item,self.__entry.name))

        def extract(self,entry,**kwargs):
            eval_proxy_ref__=__class__.__ProxyReflector(entry)
            expr=kwargs['expr'].replace('$','eval_proxy_ref__.')
            return eval(expr)
