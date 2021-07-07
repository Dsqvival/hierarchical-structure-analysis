from mir.io.feature_io_base import *
import numpy as np
import librosa

class AirIO(FeatureIO):
    def read(self, filename, entry):
        return pickle_read(self, filename)

    def write(self, data, filename, entry):
        return pickle_write(self, data, filename)

    def visualize(self, data, filename, entry, override_sr):
        arr=data.export_to_array()
        from mir.io.implement.regional_spectrogram_io import RegionalSpectrogramIO
        return RegionalSpectrogramIO().visualize(arr,filename,entry,override_sr=override_sr)

    def get_visualize_extention_name(self):
        return "svl"