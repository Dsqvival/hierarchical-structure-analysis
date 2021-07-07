from mir.io.feature_io_base import *

class ListIO(FeatureIO):

    def read(self, filename, entry):
        return pickle_read(self, filename)

    def write(self, data, filename, entry):
        pickle_write(self, data, filename)

    def visualize(self, data, filename, entry, override_sr):
        return NotImplementedError()
