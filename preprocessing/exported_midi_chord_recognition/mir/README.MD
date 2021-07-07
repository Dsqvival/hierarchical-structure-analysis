

# MIR Helper

## Description

MIR Helper is a framework for Music Information Retrieval (MIR) data manipulating, processing and visualization. Specifically, MIR Helper provides fercilities including:

1. Structural management of feature extractors, including caching and data parallel
2. Data visualization with sonic visualizer
3. Type-explicit data IO management with custom extension supported

## Installation

1. Install python 3.5+, Copy the package to python lib folder
2. Install dependencies shown in requirements.txt
3. (Optional, recommended) Install sonic visualizer, and fill the installation path to settings.py if you want to use data visualization functions.
4. (Optional, recommended) Change DEFAULT_DATA_STORAGE_PATH in settings.py to a folder in which you want to store training data, if you want to use features in nn.data_storage
5. (Optional) Install sonic annotator and corresponding vamp plugins, and fill the installation path to settings.py if you want to use pre-defined vamp extractors

## Introduction

In the following context, we will use 'mir' to denote the package, and use 'io' to denote its IO manager.
```
import mir
import mir.io as io
```

### Data Management

#### Feature IO

We define everything representable related to a certain music piece in the computer as a feature.
The wave form, the spectrogram and the symbolic data can all be a kind of feature.

A feature has its own type denoted by an IO class. The IO class controls (1) what the feature format is and how to read it from files or write it to files and (2) how the feature can be visualized with Sonic Visualizer.
All IO classes must inherit the base class FeatureIO.

Some examples:
1. io.MusicIO is the feature type for wave data. It uses mono-channel numpy array for feature representation.
It can read .wav, .mp3, .ogg, etc. files and write .wav files;
2. io.MidiIO is the feature type for midi data. It uses PrettyMidi package for feature representation. It can read or write .mid files;
3. io.SpectrogramIO is the feature type for 2d spectrogram. It uses python pickle for fast IO, and can be visualized to sonic visualizer easily.

All other features with no pre-defined type in an IO class should be assigned type 'UnknownIO'. By doing so, the feature cannot be read or written or visualized. To avoid that, you are suggested to write your own IO class to enable these features in your custom way.

#### DataEntry

DataEntry is a container specifically for storage of wave data of a song, along with all features linked with the song.
```
entry=mir.DataEntry()

# Set properties for IO
entry.prop.set('sr',22050)
entry.prop.set('hop_length',512)

# Append the raw audio from the file 'wave.mp3'
entry.append_file('wave.mp3',io.MusicIO,'music')

# Append the data whose name is 'cqt' with pre-defined type 'SpectrogramIO'
entry.append_data(cqt_data,io.SpectrogramIO,'cqt')

# Append the data whose name is 'chord' with your custom type 'CustomChordLabIO'
entry.append_data(chord_estimated,CustomChordLabIO,'chord')

# Visualize all the above features in a single window in sonic visualizer
entry.visualize(['music','cqt','chord'])

# Directly call some features by entry.feature_name to get its content
# it is equivalent to print(entry.dict['cqt'].get(entry))
print(entry.cqt.shape)
```

#### DataProxy

DataProxy is a container to hold a single feature for a song. It also works as a proxy to handle things that improve the space and the time efficiency for the program:

(1) Automatic lazy loading: load the feature only when it is needed.
(2) Automatic cache management: cache it to prevent repetitive computation in the future

The DataProxy has three subclasses which share the same interface. They are

(1) FileProxy: the feature is directly loaded from a file. Lazy loading is enabled for this kind of features.
(2) ExtractorProxy: the feature is extracted by some program (e.g., a neural network, a preprocessor, etc). Lazy loading and cache management are enabled for this kind of features.
(3) DataProxy: the feature is loaded from memory. No lazy loading or cache management is enabled for this kind of features.

You can use entry.append_file, entry.append_extractor, entry.append_data to append different kinds of DataProxy to the data entry.

#### DataPool

DataPool is a container to contain multiple songs to form a data-set. Often, songs in one data-set share same properties or require same operations (e.g., same preprocessing methods). Helper functions in DataPool helps do these things fast and easily by parallel computing.

```
dataset=mir.DataPool(name='my_dataset')

# Set common properties for all songs in the dataset
dataset.prop.set('sr',22050)
dataset.prop.set('hop_length',512)

# Append all .mp3 files in a folder and create data entries for all songs
dataset.append_folder('dataset/mp3_file_folder/','.mp3',io.MusicIO,'music')

# Append all .lab files in a folder and append them to the data entries sharing the same file names
dataset.append_folder('dataset/chord_annotation_folder/','.lab',CustomChordLabIO,'chord')

# Append the same extractor to all entries in the DataPool
entry.append_extractor(CQTExtractor,'cqt',cache_enabled=True,cqt_dim=256)

# Perform feature extraction in parallel
entry.activate_proxy('cqt',thread_number=8)

# Visualize some songs in the data-set
for entry in dataset.entries:
    entry.visualize(['music','cqt','chord'])
```

#### ExtractorProxy

You can write your own ExtractorProxy if you want to use automatic caching for your extractor. To do this, you need create a subclass of the base class ExtractorBase and implement two functions:

1. get_feature_class(self): returns what type of features it is extraction
2. extract(self,entry,**kwargs): how to perform the extraction algorithm. kwargs may contain additional parameters to the extractor.

Here is an example of a CQT extractor, which is a wrapper of the package librosa:

```
class CQTExtractor(mir.extractors.ExtractorBase):
    def get_feature_class(self):
        return io.SpectrogramIO

    def extract(self,entry,**kwargs):
        n_bins=kwargs['n_bins']
        hop_length=entry.prop.hop_length
        logspec=librosa.core.cqt(entry.music,hop_length=hop_length, bins_per_octave=36, n_bins=n_bins,
                                   filter_scale=1.5).T
        return np.abs(logspec)
```

### Integration with PyTorch

Another function of the package is to perform PyTorch-related work easier by a network trainer/inference framework.

```
import mir.nn
```

#### DataStorage

The DataStorage class and its subclasses provide a way to store different kinds of data. We know that different data types/the scales of the data lead to different solution to store the data. Thus, in typical MIR tasks, two solutions are provided:

(1) FramedRAMDataStorage is a data storage for framed data that fits in your RAM;
(2) FramedH5DataStorage is a data storage for framed data that is too large to fit in your RAM. We use H5FS to read it from disks in real-time instead.

However, they share the same interface that can be recognized with a DataProvider and a NetworkInterface.


To save to a data storage, it is encouraged to use the data management methods in this package:

```
dataset.append_extractor(mir.extractors.misc.FrameCount,'n_frame',source='cqt')
storage_cqt=mir.nn.FramedH5DataStorage('/my/storage/path/500songs_cqt',dtype=np.float16)
if(not storage_cqt.created):
    storage_cqt.create_and_cache(dataset.entries,'cqt')
```

If framed data is written, be sure to pre-calculate (or pre-cache) the 'n_frame' feature (the frame count of the data) in every data entry in the data-set. Otherwise, it would be very slow and memory-consuming.

To load from a data storage, you can do something like:

```
storage_cqt=mir.nn.FramedRAMDataStorage('/my/storage/path/500songs_cqt')
storage_cqt.load_meta()
print('We have %d songs!'%storage_cqt.get_length())
```

#### DataProvider

The data provider is a way to combine multiple DataStorage instances into one with the 'link' function. When feeding into the network, data pieces will be sampled from the same position for all DataStorage instances. These dat pieces will form into a tuple.

It will also decide whether data augmentation is performed by how you create it.

**Notice: this class is a subclass of torch.Dataset. This means you can use it in other pure PyTorch programs.**

```
train_provider=mir.nn.FramedDataProvider(train_sample_length=LSTM_TRAIN_LENGTH, # how many frames per sample
                                         shift_low=0, # what is the lower bound of pitch shift, inclusive
                                         shift_high=11, # what is the upper bound of pitch shift, inclusive
                                         num_workers=4) # how many extra threads are use to fetch data in parallel

# Link the feature storage to the data provider
train_provider.link(storage_x,CQTPitchShifter(SPEC_DIM,SHIFT_LOW,SHIFT_HIGH),subrange=train_indices)

# Link the label storage to the data provider
train_provider.link(storage_y,ChordPitchShifter(),subrange=train_indices)

# Get the total samples
length=train_provider.get_length()

# It will produce a random sample pair (x,y) where x is from storage_x and y is from storage_y
print(train_provider.get_sample(np.random.randint(length))
```

#### DataDecorator

data decorators helps you to perform final data preprocessing before training, and/or data augmentation. To write your own data decorator, create a subclass of AbstractPitchShifter and implement your own pitch_shift function. Then, pass it to the DataProvider when you link some DataStorage to it.

An example is the CQT pitch shifter where we shift pitch by performing scrolling on the frequency axis:

```
class CQTPitchShifter(AbstractPitchShifter):

    def __init__(self,spec_dim,shift_low,shift_high,shift_step=3):
        self.shift_low=shift_low
        self.shift_high=shift_high
        self.spec_dim=spec_dim
        self.shift_step=shift_step
        self.min_input_dim=(-self.shift_low+self.shift_high)*self.shift_step+self.spec_dim

    def pitch_shift(self,data,shift):
        if(data.shape[1]<self.min_input_dim):
            raise Exception('CQTPitchShifter excepted spectrogram with dim >= %d, got %d'%
                            (self.min_input_dim,data.shape[1]))
        start_dim=(-shift+self.shift_high)*self.shift_step
        return data[:,start_dim:start_dim+self.spec_dim]
```

#### NetworkInterface

NetworkInterface provides a interface for training and testing PyTorch models. To use the class, you first need to define a model structure in a subclass of mir.nn.NetworkBehavior.

You need to complete these functions in your subclass:

(1) \_\_init\_\_(self): initialize what you want to initialize.
(2) forward(self, x): the same as torch.nn.Module.forward. PyTorch hooks work here.
(3) loss(self, *args): how to calculate the loss. args are the tuples from the data provider with each element converted to PyTorch format
(4) inference(self, x): how do you plan to do the inference.

After that, you can use a NetworkInterface to wrap the class you defined, and train the network.

Here is an example of training a network with cross validation:

```
import sys
import numpy as np
TOTAL_FOLD_COUNT=5
slice_id=int(sys.argv[1])
if(slice_id>=5 or slice_id<0):
    raise Exception('Invalid input')
print('Train on slice %d'%slice_id)
storage_x=mir.nn.FramedH5DataStorage('/path/to/storage/cqt')
storage_y=mir.nn.FramedH5DataStorage('/path/to/storage/chord')
storage_x.load_meta()
song_count=storage_x.get_length()
is_training=np.ones(song_count,dtype=np.bool)
is_validation=np.zeros(song_count,dtype=np.bool)
is_testing=np.zeros(song_count,dtype=np.bool)
for i in range(song_count):
    if(i%TOTAL_FOLD_COUNT==slice_id):
        is_training[i]=False
        is_testing[i]=True
    if((i+1)%TOTAL_FOLD_COUNT==slice_id):
        is_training[i]=False
        is_validation[i]=True
train_indices=np.arange(song_count)[is_training]
val_indices=np.arange(song_count)[is_validation]
print('Using %d samples to train'%len(train_indices))
print('Using %d samples to validate'%len(val_indices))
train_provider=mir.nn.FramedDataProvider(train_sample_length=LSTM_TRAIN_LENGTH,shift_low=SHIFT_LOW,shift_high=SHIFT_HIGH,num_workers=4)
train_provider.link(storage_x,CQTPitchShifter(SPEC_DIM,SHIFT_LOW,SHIFT_HIGH),subrange=train_indices)
train_provider.link(storage_y,ChordPitchShifter(),subrange=train_indices)

val_provider=mir.nn.FramedDataProvider(train_sample_length=LSTM_TRAIN_LENGTH,shift_low=SHIFT_LOW,shift_high=SHIFT_HIGH,num_workers=4)
val_provider.link(storage_x,CQTPitchShifter(SPEC_DIM,SHIFT_LOW,SHIFT_HIGH),subrange=val_indices)
val_provider.link(storage_y,ChordPitchShifter(),subrange=val_indices)

# Create an instance of NetworkInterface
trainer=mir.nn.NetworkInterface(
    MyNetworkModel(), # this is your model
    'model_fold=%d(p)'%slice_id, # model cache name
    load_checkpoint=True # load model state from checkpoint?
)
# Train the network
trainer.train_supervised(
    train_provider, # training set data provider
    val_provider, # validation set data provider
    batch_size=96, # batch size
    learning_rates_dict={1e-3:6,1e-4:3,1e-5:3}, # learning rate change after certain epochs (decay function is currently not supported)
    round_per_print=10,
    round_per_val=50,
    round_per_save=500
)
```

The marked '\(p\)' in the model indicates that it will perform parallel training. Otherwise, it will only use 1 gpu/cpu.

After training, you can call NetworkInterface.inference(input) to calculate the model output given the input.