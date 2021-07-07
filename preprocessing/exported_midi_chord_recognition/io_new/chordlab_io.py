from mir.io.feature_io_base import *
from mir.common import PACKAGE_PATH
import numpy as np

class ChordLabIO(FeatureIO):
    def read(self, filename, entry):
        f = open(filename, 'r')
        content = f.read()
        lines=content.split('\n')
        f.close()
        result=[]
        for i in range(len(lines)):
            line=lines[i].strip()
            if(line==''):
                continue
            tokens=line.split('\t')
            assert(len(tokens)==3)
            result.append([float(tokens[0]),float(tokens[1]),tokens[2]])
        return result

    def write(self, data, filename, entry):
        f = open(filename, 'w')
        for i in range(0, len(data)):
            f.write('\t'.join([str(item) for item in data[i]]))
            f.write('\n')
        f.close()

    def visualize(self, data, filename, entry, override_sr):
        sr = override_sr
        f = open(os.path.join(PACKAGE_PATH,'data/sparse_tag_template.svl'), 'r')
        content = f.read()
        f.close()
        content = content.replace('[__SR__]', str(sr))
        content = content.replace('[__STYLE__]', str(1))
        results=[]
        for item in data:
            results.append('<point frame="%d" label="%s" />'%(int(np.round(item[0]*sr)),item[2]))
        content=content.replace('[__DATA__]','\n'.join(results))
        f=open(filename,'w')
        f.write(content)
        f.close()

    def get_visualize_extention_name(self):
        return "svl"