from mir.io.feature_io_base import *
import numpy as np
import librosa
import codecs

class LyricIO(FeatureIO):
    def read(self, filename, entry):
        f = open(filename, 'r', encoding='utf-16-le')
        content = f.read()
        if(content.startswith('\ufeff')):
            content=content[1:]
        lines=content.split('\n')
        f.close()
        result=[]
        for i in range(len(lines)):
            line=lines[i].strip()
            if(line==''):
                continue
            tokens=line.split('\t')
            if(len(tokens)==3):
                result.append([float(tokens[0]),float(tokens[1]),tokens[2]])
            elif(len(tokens)==4): # Contains sentence information
                result.append([float(tokens[0]),float(tokens[1]),tokens[2],int(tokens[3])])
            else:
                raise Exception('Not supported format')
        return result

    def write(self, data, filename, entry):
        f = open(filename, 'wb')
        f.write(codecs.BOM_UTF16_LE)
        for i in range(0, len(data)):
            f.write('\t'.join([str(item) for item in data[i]]).encode('utf-16-le'))
            f.write('\n'.encode('utf-16-le'))
        f.close()

    def visualize(self, data, filename, entry, override_sr):
        f = open(filename, 'w')
        for i in range(0, len(data)):
            f.write('\t'.join([str(item) for item in data[i]]))
            f.write('\n')
        f.close()

    def get_visualize_extention_name(self):
        return "txt"