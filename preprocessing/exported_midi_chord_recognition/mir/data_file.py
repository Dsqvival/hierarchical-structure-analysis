from abc import ABC,abstractmethod
from mir.common import SONIC_VISUALIZER_PATH,WORKING_PATH
import subprocess
import os
import gc
import mir.io
from joblib import Parallel,delayed
import random
from pydub.utils import mediainfo
import time
import datetime
import mir.cache



class ProxyBase(ABC):
    def __init__(self,feature_class):
        self.loaded=False
        self.loaded_data=None
        self.feature_class=feature_class

    def pre_assign(self, entry):
        io = self.feature_class()
        io.pre_assign(entry, self)

    def get(self,requester):
        if(not self.loaded):
            self.loaded_data=self.load(requester)
            self.post_load(requester)
            self.loaded=True
        return self.loaded_data

    @abstractmethod
    def load(self, requester):
        pass

    def post_load(self, requester):
        io = self.feature_class()
        io.post_load(self.loaded_data, requester)

    def unload(self,gc_collect=True):
        if(self.loaded):
            self.loaded=False
            del self.loaded_data
            if(gc_collect):
                gc.collect()

    def save_visualize_temp_file(self,requestor,savepath,auralize,override_sr,beats=None):
        io = self.feature_class()
        if(auralize):
            if(beats is not None):
                io.auralize_with_beat(self.get(requestor),savepath,requestor,beats)
            else:
                io.auralize(self.get(requestor), savepath, requestor)
        else:
            io.visualize(self.get(requestor),savepath,requestor,override_sr)


class FileProxy(ProxyBase):
    def __init__(self,file_path,feature_class,file_exist_check=True):
        super().__init__(feature_class)
        # if file_path is absolute, the statement will have no effect
        file_path=os.path.join(WORKING_PATH,file_path)
        if (file_exist_check and (not os.path.isfile(file_path))):
            raise Exception("File not found: %s"%file_path)
        self.filepath=file_path

    def load(self,requester):
        io = self.feature_class()
        return io.safe_read(self.filepath, requester)


class ExtractorProxy(ProxyBase):
    def __init__(self,extractor_class,cache_enabled=True,io_override=None,**kwargs):
        self.extractor=extractor_class()
        if(io_override is not None):
            feature_class=io_override
        else:
            feature_class=self.extractor.get_feature_class()
        super().__init__(feature_class)
        self.kwargs=kwargs
        self.cache_enabled=cache_enabled

    def load(self, requester):
        return self.extractor.extract_and_cache(requester,self.cache_enabled,**self.kwargs)


class DataProxy(ProxyBase):
    def __init__(self,data,feature_class):
        super().__init__(feature_class)
        self.loaded_data=data
        self.loaded=True

    def load(self,requester):
        raise Exception('Shouldn\'t be here!')

    def unload(self,gc_collect=True):
        pass

class ProxyArray():
    def __init__(self, name, entry):
        self.name=name
        self.entry=entry

    def __getitem__(self, item):
        return self.entry.__getattr__(self.name+'['+str(item)+']')


class TextureBuilder():
    def __init__(self, texture_class, chords_item, beats_item):
        self.texture_class=texture_class
        self.chords_item=chords_item
        self.beats_item=beats_item


class DataEntryProperties():
    def __init__(self):
        self.dict={}
        self.recorded_set_stack=[]
        self.recording=True

    def __getattr__(self, item):
        return self.get(item)

    def remove(self, item):
        del self.dict[item]

    def set(self, item, value):
        if('dict' not in self.__dict__):
            raise AttributeError('you are not initialized!')
        if(isinstance(value,mir.io.LoadingPlaceholder)):
            # Set a place holder
            if (item not in self.dict):
                self.dict[item] = value
        elif(item in self.dict and not isinstance(self.dict[item],mir.io.LoadingPlaceholder)):
            # Old value found
            if(self.dict[item]!=value):
                print('Warning: Inconsistant property in %s: old value'%item,self.dict[item],'new value',value)
        else:
            # No old value, set a new value
            self.dict[item]=value

    def get(self,item):
        if('dict' not in self.__dict__):
            raise AttributeError('you are not initialized!')
        if(item in self.dict):
            if(len(self.recorded_set_stack)>0): # Recording
                self.recorded_set_stack[-1].add(item)
            obj=self.dict[item]
            if(isinstance(obj,mir.io.LoadingPlaceholder)):
                obj.fire()
                obj=self.dict[item]
                assert(not isinstance(obj,mir.io.LoadingPlaceholder))
            return obj
        else:
            raise AttributeError("Property %s not appended!"%item)

    def get_unrecorded(self,item):
        if('dict' not in self.__dict__):
            raise AttributeError('you are not initialized!')
        if(item in self.dict):
            obj=self.dict[item]
            if(isinstance(obj,mir.io.LoadingPlaceholder)):
                obj.fire()
                obj=self.dict[item]
                assert(not isinstance(obj,mir.io.LoadingPlaceholder))
            return obj

    def start_record_reading(self):
        self.recorded_set_stack.append(set())

    def end_record_reading(self):
        result=self.recorded_set_stack.pop()
        return list(result)


class DataEntry():
    # Warning: use empty name will disable all extractors' cache
    def __init__(self,name=''):
        self.dict={}
        self.name=name
        self.prop=DataEntryProperties()
        self.proxy_array=set()

    def __getattr__(self, item):
        if('dict' not in self.__dict__):
            raise AttributeError('you are not initialized!')
            # I wonder, why someone would intentionally create a DataEntry
            # whose __dict__ is {} to run something multi-threadly
        if(item in self.dict):
            return self.dict[item].get(self)
        elif(item in self.proxy_array):
            return ProxyArray(item,entry=self)
        else:
            raise AttributeError("Datatype %s not appended!"%item)

    def has(self,item):
        return item in self.dict

    def rename(self,old_name,new_name):
        if(old_name!=new_name):
            self.dict[new_name]=self.dict[old_name]
            del self.dict[old_name]

    def swap(self,item1,item2):
        temp_item=self.dict[item1]
        self.dict[item1]=self.dict[item2]
        self.dict[item2]=temp_item

    def remove(self,item):
        del self.dict[item]

    def free(self,item='',gc_collect=True):
        if(item==''):
            for del_item in self.dict:
                self.dict[del_item].unload(gc_collect)
        else:
            self.dict[item].unload(gc_collect)

    def append_file(self,filename,feature_class,output_name,file_exist_check=True):
        file_proxy=FileProxy(filename,feature_class,file_exist_check=file_exist_check)
        file_proxy.pre_assign(self)
        self.dict[output_name]=file_proxy

    def apply_extractor(self,extractor_class,cache_enabled=True,io_override=None,**kwargs):
        extractor_proxy=ExtractorProxy(extractor_class,cache_enabled,io_override,**kwargs)
        extractor_proxy.pre_assign(self)
        return extractor_proxy.get(self)

    def append_extractor(self,extractor_class,output_name,cache_enabled=True,io_override=None,**kwargs):
        extractor_proxy=ExtractorProxy(extractor_class,cache_enabled,io_override,**kwargs)
        extractor_proxy.pre_assign(self)
        self.dict[output_name]=extractor_proxy

    def append_data(self,data,feature_class,output_name):
        data_proxy=DataProxy(data,feature_class)
        data_proxy.pre_assign(self)
        self.dict[output_name]=data_proxy

    def declare_proxy_array(self,name):
        if(name in self.proxy_array):
            return
        self.proxy_array.add(name)

    def activate_proxy(self, item, free=False, verbose_id=0, verbose_all=0, start_time=None):
        if(verbose_all>0):
            if(verbose_id > 0 and start_time is not None):
                current_time=time.time()
                print('[%d/%d]Activating %s, passed:'%(verbose_id,verbose_all,item),
                      str(datetime.timedelta(seconds=current_time-start_time)),'remaining:',
                      str(datetime.timedelta(seconds=(current_time-start_time)/verbose_id*(verbose_all-verbose_id))),flush=True)
            else:
                print('[%d/%d]Activating %s'%(verbose_id,verbose_all,item),flush=True)
        self.dict[item].get(self)
        if(free):
            self.free('')

    def save(self, item, filename, create_dir=False):
        if(create_dir):
            mir.cache.mkdir_for_file(filename)
        self.dict[item].feature_class().write(self.dict[item].get(self),filename,self)

    def visualize(self,items=None,use_raw_music_file=True,music='music',midi_texture_builder: TextureBuilder=None):
        if(items==None):
            items=[]
        elif(not isinstance(items,list)):
            items=[items]
        temp_path=os.path.join(WORKING_PATH,'temp')
        if(not os.path.isdir(temp_path)):
            os.makedirs(temp_path)
        result_string='"'+SONIC_VISUALIZER_PATH+'" '
        if(use_raw_music_file):
            if(isinstance(music,list)):
                music_list=music
            else:
                music_list=[music]
            for music_item in music_list:
                if (not isinstance(self.dict[music_item],FileProxy)):
                    # Well, there is no raw music file at all
                    items.insert(0,music_item)
                    override_sr=self.prop.get_unrecorded('sr')
                else:
                    filepath=os.path.join(WORKING_PATH, self.dict[music_item].filepath)
                    result_string += '"' + filepath + '" '
                    info = mediainfo(filepath)
                    override_sr=int(info['sample_rate'])
        else:
            override_sr=self.prop.get_unrecorded('sr')
        temp_file_list=[]
        for item in items:
            if(self.has(item)):
                abbr='_visualize.' + self.dict[item].feature_class().get_visualize_extention_name()
                temp_file_name=os.path.join(temp_path,item+abbr)
                temp_file_list.append(temp_file_name)
                result_string+='"'+temp_file_name+'" '
                self.dict[item].save_visualize_temp_file(self,temp_file_name,auralize=False,override_sr=override_sr)
            else:
                raise Exception('No such feature to visualize: %s'%item)

        if(midi_texture_builder is not None):
            chords_item=midi_texture_builder.chords_item
            beats_item=midi_texture_builder.beats_item
            if(self.has(chords_item)):
                abbr='_auralize.svl'
                temp_file_name=os.path.join(temp_path,chords_item+abbr)
                temp_file_list.append(temp_file_name)
                result_string+='"'+temp_file_name+'" '
                if(beats_item!=None):
                    beats=self.dict[beats_item].get(self)
                else:
                    beats=None
                generator=midi_texture_builder.texture_class()

                sr = self.prop.get_unrecorded('sr')
                win_shift = self.prop.get_unrecorded('hop_length')
                generator.auralize(filename=temp_file_name,chords=self.dict[chords_item].get(self),beats=beats,
                                   sr=sr,win_shift=win_shift)
            else:
                raise Exception('No such feature to auralize: %s'%chords_item)

        return_code=subprocess.call(result_string.replace('\\','/'))

        # Delete temp files
        for path in temp_file_list:
            try:
                os.unlink(path)
            except:
                print('[Warning] Temp file delete failed:',path)
        return return_code


class DataPool:
    def __init__(self,name,**default_properties):
        self.entries=[]
        self.dict={} # collections.OrderedDict()
        self.name=name
        self.antidict=[]
        self.default_prop={}
        for (k,v) in default_properties:
            self.default_prop[k]=v

    def __getitem__(self, key):
        if(isinstance(key,slice)):
            sub_indices=range(len(self.entries))[key]
            sub_pool=DataPool(self.name)
            for i in sub_indices:
                sub_pool.__append_entry(self.entries[i],self.antidict[i])
            return sub_pool
        else:
            if(isinstance(key,int)):
                raise Exception('Use dataset.entries to iterate over its entries')
            raise Exception('Unsupported slicing type:',key)

    def __append_entry(self,entry,entry_name):
        lower_entry_name=entry_name.lower()
        if(lower_entry_name in self.dict):
            print('Warning: entry `%s` overriding %s'%(entry.name,entry_name))
        self.dict[lower_entry_name]=entry
        self.antidict.append(lower_entry_name)
        self.entries.append(entry)

    def remove_entry(self,entry):
        # todo: more situtations
        if('/' in entry.name):
            entry_name=entry.name[entry.name.index('/')+1:]
        else:
            entry_name=entry.name
        lower_entry_name=entry_name.lower()
        del self.dict[lower_entry_name]
        self.antidict.remove(lower_entry_name)
        self.entries.remove(entry)

    def add_entry(self,entry):
        filename=entry.name.split('/')[-1]
        if(filename==''):
            raise Exception('Cannot add entry whose name is empty')
        if('&' in self.name):
            print('Warning: You are adding an entry to a joint dataset. Don\'t do that!')
        elif(entry.name.split('/')[0]!=self.name):
            print('Warning: Inconsistent dataset name, %s expected, %s found'%(self.name,entry.name.split('/')[0]))
        self.__append_entry(entry,filename)

    def set_property(self,key,value):
        self.default_prop[key]=value

    def new_entry(self,filename):
        if('&' in self.name):
            print('Warning: You are creating an entry in a joint dataset. Don\'t do that!')
        entry = DataEntry(self.name+'/'+filename)
        lower_filename=filename.lower()
        if(lower_filename in self.dict):
            print('Warning: Entry name overwrite: %s'%filename)
        for k in self.default_prop:
            entry.prop.set(k, self.default_prop[k])
        self.__append_entry(entry,filename)
        return entry

    def append_folder(self,folder_path,suffix,typename,output_name,recursive=False):
        if(recursive):
            files=[os.path.join(dp, f).replace('\\','/') for dp, dn, fn in os.walk(folder_path) for f in fn]
        else:
            files=[os.path.join(folder_path, f) for f in os.listdir(folder_path)]
        # if it's run for the first time, create the dict
        if(len(self.dict)==0):
            for file in files:
                if file.endswith(suffix):
                    filename = os.path.basename(file)
                    filename = filename[:len(filename) - len(suffix)]
                    entry = DataEntry(self.name+'/'+filename)
                    entry.append_file(file, typename, output_name=output_name, file_exist_check=False)
                    for k in self.default_prop:
                        entry.prop.set(k, self.default_prop[k])
                    self.__append_entry(entry,filename)
            # sorted order
            # for (k,entry) in self.dict.items():
            #     self.entries.append(entry)
            if(len(self.dict)==0):
                print('Warning: No data entry was created in "%s"'%folder_path)
        else: # check the dict
            mark={}
            for file in files:
                if file.endswith(suffix):
                    filename=os.path.basename(file)
                    filename=filename[:len(filename)-len(suffix)]
                    lower_filename=filename.lower()
                    if(lower_filename in self.dict):
                        entry=self.dict[lower_filename]
                        entry.append_file(file,typename,output_name=output_name,file_exist_check=False)
                        mark[lower_filename]=True
            delta=len(self.dict)-len(mark)
            if(delta!=0):
                print('Warning: %d entries not appended in "%s"'%(delta,folder_path))
                if(delta>10):
                    print('Some of them are:')
                    delta=10
                else:
                    print('They are:')
                for (k,v) in self.dict.items():
                    if(k not in mark):
                        print(k)
                        delta-=1
                        if(delta==0):
                            break

    def append_extractor(self,extractor_class,output_name,cache_enabled=True,io_override=None,**kwargs):
        for entry in self.entries:
            entry.append_extractor(extractor_class,output_name,cache_enabled=cache_enabled,io_override=io_override,**kwargs)

    def activate_proxy(self,item,thread_number=1,timing=True,free=False):
        entries_needs = [entry for entry in self.entries if not entry.dict[item].loaded]
        total=len(entries_needs)
        print('Total %s: %d entries to activate' % (item,total))
        start_time=time.time() if timing else None
        if(thread_number!=1):
            random.shuffle(entries_needs)
            Parallel(n_jobs=thread_number)(delayed(DataEntry.activate_proxy)(entries_needs[i],item,free,i,total,start_time) for i in range(len(entries_needs)))
        else:
            for i in range(len(entries_needs)):
                entries_needs[i].activate_proxy(item,free,i,total,start_time)

    def free(self, item='', gc_collect=True):
        if(item==''):
            for e in self.entries:
                for del_item in e.dict:
                    e.dict[del_item].unload(gc_collect=False)
        else:
            for e in self.entries:
                e.dict[item].unload(gc_collect=False)
        if(gc_collect):
            gc.collect()

    def subrange(self,*args):
        subpool=DataPool(self.name)
        for i in range(*args):
            subpool.__append_entry(self.entries[i],self.antidict[i])
        return subpool

    def sublist(self,arg):
        subpool=DataPool(self.name)
        for i in arg:
            subpool.__append_entry(self.entries[i],self.antidict[i])
        return subpool


    def find(self,name):
        for entry in self.entries:
            if(name.lower() in entry.name.lower()):
                return entry
        raise Exception('Cannot find %s in %s'%(name,self.name))

    def where(self,name):
        subpool=DataPool(self.name)
        for i in range(len(self.entries)):
            entry=self.entries[i]
            if(name.lower() in entry.name.lower()):
                subpool.__append_entry(entry,self.antidict[i])
        return subpool

    def random_choice(self,count=1):
        import random
        return self.sublist(random.sample(range(len(self.entries)),count))

    def join(*args):
        result_pool=DataPool(' & '.join([dataset.name for dataset in args]))
        for dataset in args:
            for i in range(len(dataset.entries)):
                result_pool.__append_entry(dataset.entries[i],dataset.entries[i].name)
                # For joint dataset, the keys in the look-up dictionary self.dict
                # will be formatted as `original_dataset/entry_file_name` instead of
                # `entry_file_name`
        return result_pool

