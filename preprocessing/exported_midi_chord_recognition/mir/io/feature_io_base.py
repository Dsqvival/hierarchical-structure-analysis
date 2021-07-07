from abc import ABC,abstractmethod
import pickle
import os

class LoadingPlaceholder():
    def __init__(self,proxy,entry):
        self.proxy=proxy
        self.entry=entry
        pass

    def fire(self):
        self.proxy.get(self.entry)

class FeatureIO(ABC):

    @abstractmethod
    def read(self, filename, entry):
        pass

    def safe_read(self, filename, entry):
        entry.prop.start_record_reading()
        try:
            result=self.read(filename,entry)
        except Exception:
            entry.prop.end_record_reading()
            raise
        entry.prop.end_record_reading()
        return result

    def try_mkdir(self, filename):
        folder=os.path.dirname(filename)
        if(not os.path.isdir(folder)):
            os.makedirs(folder)

    def create(self, data, filename, entry):
        self.try_mkdir(filename)
        self.write(data,filename,entry)

    @abstractmethod
    def write(self, data, filename, entry):
        pass

    # override iif writing and visualizing use different methods
    # (i.e. compressed vs uncompressed)
    def visualize(self, data, filename, entry, override_sr):
        self.write(data, filename, entry)

    # override iff entry properties will be updated upon loading
    def pre_assign(self, entry, proxy):
        pass

    # override iff entry properties need updated upon loading
    def post_load(self, data, entry):
        pass

    # override iif it will save as other formats (e.g. wav)
    def get_visualize_extention_name(self):
        return "txt"

    def file_to_evaluation_format(self, filename, entry):
        raise Exception('Not supported by the io class')

    def data_to_evaluation_format(self, data, entry):
        raise Exception('Not supported by the io class')


def pickle_read(self, filename):
    f = open(filename, 'rb')
    obj = pickle.load(f)
    f.close()
    return obj

def pickle_write(self, data, filename):
    f = open(filename, 'wb')
    pickle.dump(data, f)
    f.close()


def create_svl_3d_data(labels, data):
    assert (len(labels) == data.shape[1])
    results_part1 = ['<bin number="%d" name="%s"/>' % (i, str(labels[i])) for i in range(len(labels))]
    results_part2 = ['<row n="%d">%s</row>' % (i, ' '.join([
        str(s) for s in data[i]
    ])) for i in range(data.shape[0])]
    return '\n'.join(results_part1) + '\n' + '\n'.join(results_part2)


def framed_2d_feature_visualizer(entry,features, filename):
    f = open(filename, 'w')
    for i in range(0, features.shape[0]):
        time = entry.prop.hop_length * i / entry.prop.sr
        f.write(str(time))
        for j in range(0, features.shape[1]):
            f.write('\t' + str(features[i][j]))
        f.write('\n')
    f.close()