from abc import ABC,abstractmethod
from mir.common import WORKING_PATH
from mir import io
import os
import pickle

def pickle_read(filename):
    f = open(filename, 'rb')
    obj = pickle.load(f)
    f.close()
    return obj

def pickle_write(data, filename):
    f = open(filename, 'wb')
    pickle.dump(data, f)
    f.close()

def try_mkdir(filename):
    folder=os.path.dirname(filename)
    if(not os.path.isdir(folder)):
        os.makedirs(folder)

class ExtractorBase(ABC):

    def require(self, *args):
        pass

    def get_feature_class(self):
        return io.UnknownIO

    @abstractmethod
    def extract(self,entry,**kwargs):
        pass

    def __create_cache_path(self,entry,cached_prop_record,input_kwargs):

        items={}
        items_entry={}
        for k in input_kwargs:
            items[k]=input_kwargs[k]
        for prop_name in cached_prop_record:
            if(prop_name not in items):
                items_entry[prop_name]=entry.prop.get_unrecorded(prop_name)

        if(len(items)==0):
            folder_name=self.__class__.__name__
        else:
            folder_name=self.__class__.__name__+'/'+','.join([k+'='+str(items[k]) for k in sorted(items.keys())])

        if(len(items_entry)==0):
            entry_name=entry.name+'.cache'
        else:
            entry_name=entry.name+'.'+','.join([k+'='+str(items_entry[k]) for k in sorted(items_entry.keys())])+'.cache'

        return os.path.join(WORKING_PATH, 'cache_data', folder_name, entry_name)


    def extract_and_cache(self,entry,cache_enabled=True,**kwargs):
        folder_name=os.path.join(WORKING_PATH, 'cache_data',self.__class__.__name__)
        prop_cache_filename=os.path.join(folder_name,'_prop_records.cache')
        if('cached_prop_record' in self.__dict__):
            cached_prop_record=self.__dict__['cached_prop_record']
        else:
            if(os.path.exists(prop_cache_filename)):
                cached_prop_record=pickle_read(prop_cache_filename)
            else:
                cached_prop_record=None

        if(cache_enabled and entry.name!='' and self.get_feature_class()!=io.UnknownIO):
            # Need cache
            need_io_create=False
            if(cached_prop_record is None):
                entry.prop.start_record_reading()
                feature=self.extract(entry,**kwargs)
                cached_prop_record=sorted(entry.prop.end_record_reading())
                try_mkdir(prop_cache_filename)
                pickle_write(cached_prop_record,prop_cache_filename)
                cache_file_name=self.__create_cache_path(entry,cached_prop_record,kwargs)
                need_io_create=True
            else:
                cache_file_name=self.__create_cache_path(entry,cached_prop_record,kwargs)
                if(not os.path.isfile(cache_file_name)):
                    entry.prop.start_record_reading()
                    feature=self.extract(entry,**kwargs)
                    new_prop_record=sorted(entry.prop.end_record_reading())
                    if(cached_prop_record!=new_prop_record):
                        print('[Warning] Inconsistent cached properity requirement in %s, overrode:'%self.__class__.__name__)
                        print('Old:',cached_prop_record)
                        print('New:',new_prop_record)
                        cached_prop_record=new_prop_record
                        pickle_write(cached_prop_record,prop_cache_filename)
                        cache_file_name = self.__create_cache_path(entry, cached_prop_record, kwargs)
                    need_io_create=True
                else:
                    io_obj=self.get_feature_class()()
                    feature=io_obj.safe_read(cache_file_name,entry)
            if(need_io_create):
                io_obj=self.get_feature_class()()
                io_obj.create(feature,cache_file_name,entry)
        else:
            feature = self.extract(entry, **kwargs)
        return feature





