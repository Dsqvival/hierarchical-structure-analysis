from mir.io.feature_io_base import *

class UnknownIO(FeatureIO):

    def read(self, filename, entry):
        raise Exception('Unknown type cannot be read')

    def write(self, data, filename, entry):
        raise Exception('Unknown type cannot be written')

    def visualize(self, data, filename, entry, override_sr):
        raise Exception('Unknown type cannot be visualized')