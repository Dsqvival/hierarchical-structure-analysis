from mir.io.feature_io_base import *


class FloatIO(FeatureIO):
    def read(self, filename, entry):
        f=open(filename,'r')
        result=float(f.readline().strip())
        f.close()
        return result

    def write(self, data, filename, entry):
        f=open(filename,'w')
        f.write(str(float(data)))
        f.close()

    def visualize(self, data, filename, entry, override_sr):
        raise Exception('Cannot visualize a scalar')

class IntegerIO(FeatureIO):
    def read(self, filename, entry):
        f=open(filename,'r')
        result=int(f.readline().strip())
        f.close()
        return result

    def write(self, data, filename, entry):
        f=open(filename,'w')
        f.write(str(int(data)))
        f.close()

    def visualize(self, data, filename, entry, override_sr):
        raise Exception('Cannot visualize a scalar')
