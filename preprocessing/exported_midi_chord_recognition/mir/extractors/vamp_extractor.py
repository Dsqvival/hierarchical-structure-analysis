from mir.extractors.extractor_base import *
from mir.common import WORKING_PATH,SONIC_ANNOTATOR_PATH,PACKAGE_PATH
from mir.cache import hasher
import numpy as np
import subprocess

def rewrite_extract_n3(entry,inputfilename,outputfilename):
    f=open(inputfilename,'r')
    content=f.read()
    f.close()
    content=content.replace('[__SR__]',str(entry.prop.sr))
    content=content.replace('[__WIN_SHIFT__]',str(entry.prop.hop_length))
    content=content.replace('[__WIN_SIZE__]',str(entry.prop.win_size))
    if(not os.path.isdir(os.path.dirname(outputfilename))):
        os.makedirs(os.path.dirname(outputfilename))
    f=open(outputfilename,'w')
    f.write(content)
    f.close()


class NNLSChroma(ExtractorBase):

    def get_feature_class(self):
        return io.ChromaIO

    def extract(self,entry,**kwargs):
        print('NNLSChroma working on entry '+entry.name)
        if('margin' in kwargs):
            if(kwargs['margin']>0):
                music=entry.music_h
            else:
                raise Exception('Error margin')

        else:
            music=entry.music
        music_io=io.MusicIO()
        temp_path=os.path.join(WORKING_PATH,'temp/nnlschroma_extractor_%s.wav'%hasher(entry.name))
        temp_n3_path=temp_path+'.n3'
        rewrite_extract_n3(entry,os.path.join(PACKAGE_PATH,'data/bothchroma.n3'),temp_n3_path)
        music_io.write(music,temp_path,entry)
        proc=subprocess.Popen([SONIC_ANNOTATOR_PATH,
                               '-t',temp_n3_path,
                               temp_path,
                               '-w','lab','--lab-stdout'
                               ],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        # print('Begin processing')
        result=np.zeros((0,24))
        for line in proc.stdout:
            # the real code does filtering here
            line=bytes.decode(line)
            if(line.endswith('\r\n')):
                line=line[:len(line)-2]
            if (line.endswith('\r')):
                line=line[:len(line)-1]
            arr=np.array(list(map(float,line.split('\t')))[1:])
            arr=arr.reshape((2,12))[::-1].T
            arr=np.roll(arr,-3,axis=0).reshape((1,24))
            result=np.append(result,arr,axis=0)
        try:
            os.unlink(temp_path)
            os.unlink(temp_n3_path)
        except:
            pass
        if(result.shape[0]==0):
            raise Exception('Empty response')
        return result


class TunedLogSpectrogram(ExtractorBase):

    def get_feature_class(self):
        return io.SpectrogramIO

    def extract(self,entry,**kwargs):
        print('TunedLogSpectrogram working on entry '+entry.name)
        music_io = io.MusicIO()
        temp_path=os.path.join(WORKING_PATH,'temp/tunedlogspectrogram_extractor_%s.wav'%hasher(entry.name))
        temp_n3_path=temp_path+'.n3'
        rewrite_extract_n3(entry,os.path.join(PACKAGE_PATH,'data/tunedlogfreqspec.n3'),temp_n3_path)
        music_io.write(entry.music,temp_path,entry)
        proc=subprocess.Popen([SONIC_ANNOTATOR_PATH,
                               '-t',temp_n3_path,
                               temp_path,
                               '-w','lab','--lab-stdout'
                               ],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        # print('Begin processing')
        result=np.zeros((0,256))
        for line in proc.stdout:
            # the real code does filtering here
            line=bytes.decode(line)
            if(line.endswith('\r\n')):
                line=line[:len(line)-2]
            if (line.endswith('\r')):
                line=line[:len(line)-1]
            arr=np.array(list(map(float,line.split('\t')))[1:])
            arr=arr.reshape((1,-1))
            result=np.append(result,arr,axis=0)
        try:
            os.unlink(temp_path)
            os.unlink(temp_n3_path)
        except:
            pass
        if(result.shape[0]==0):
            raise Exception('Empty response')
        return result

class GlobalTuning(ExtractorBase):

    def get_feature_class(self):
        return io.FloatIO
    
    def extract(self,entry,**kwargs):
        music_io = io.MusicIO()
        temp_path=os.path.join(WORKING_PATH,'temp/tuning_%s.wav'%hasher(entry.name))
        temp_n3_path=temp_path+'.n3'
        rewrite_extract_n3(entry,os.path.join(PACKAGE_PATH,'data/tuning.n3'),temp_n3_path)
        if('source' in kwargs):
            music=entry.dict[kwargs['source']].get(entry)
        else:
            music=entry.music
        music_io.write(music,temp_path,entry)
        proc=subprocess.Popen([SONIC_ANNOTATOR_PATH,
                               '-t',temp_n3_path,
                               temp_path,
                               '-w','lab','--lab-stdout'
                               ],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        # print('Begin processing')
        output=proc.stdout.readlines()
        result=(np.log2(np.float64(output[0].decode().split('\t')[2]))-np.log2(440))*12
        try:
            os.unlink(temp_path)
            os.unlink(temp_n3_path)
        except:
            pass
        return result

