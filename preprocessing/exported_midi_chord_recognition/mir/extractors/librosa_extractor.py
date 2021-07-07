from mir.extractors.extractor_base import *
import librosa
import numpy as np

class HPSS(ExtractorBase):

    def get_feature_class(self):
        return io.MusicIO

    def extract(self,entry,**kwargs):
        if('source' in kwargs):
            y=entry.dict[kwargs['source']].get(entry)
        else:
            y=entry.music
        y_h=librosa.effects.harmonic(y,margin=kwargs['margin'])
        #y_h, y_p = librosa.effects.hpss(y, margin=(1.0, 5.0))
        return y_h

class CQT(ExtractorBase):
    def get_feature_class(self):
        return io.SpectrogramIO

    # Warning this spectrum has a 1/3 half note stepping
    def extract(self,entry,**kwargs):
        n_bins = 262
        y = entry.music
        logspec = librosa.core.cqt(y, sr=kwargs['sr'], hop_length=kwargs['hop_length'], bins_per_octave=36, n_bins=n_bins,
                                   filter_scale=1.5).T
        logspec = np.abs(logspec)
        return logspec

class STFT(ExtractorBase):
    def get_feature_class(self):
        return io.SpectrogramIO

    # Warning this spectrum has a 1/3 half note stepping
    def extract(self,entry,**kwargs):
        y = entry.music
        logspec = librosa.core.stft(y, win_length=kwargs['win_size'], hop_length=kwargs['hop_length']).T
        logspec = np.abs(logspec)
        return logspec


class Onset(ExtractorBase):
    def get_feature_class(self):
        return io.SpectrogramIO

    def extract(self,entry,**kwargs):
        onset=librosa.onset.onset_strength(entry.music,sr=kwargs['sr'], hop_length=kwargs['hop_length']).reshape((-1,1))
        return onset

class Energy(ExtractorBase):
    def get_feature_class(self):
        return io.SpectrogramIO

    def extract(self,entry,**kwargs):
        energy=librosa.feature.rmse(y=entry.dict[kwargs['source']].get(entry), hop_length=kwargs['hop_length'],
                                    frame_length=kwargs['win_size'],center=True).reshape((-1,1))
        return energy
