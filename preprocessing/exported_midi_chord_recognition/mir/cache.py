import pickle
import os
from mir.common import WORKING_PATH
import hashlib

__all__=['load','save']

def mkdir_for_file(path):
    folder_path=os.path.dirname(path)
    if(not os.path.isdir(folder_path)):
        os.makedirs(folder_path)
    return path

def dumptofile(obj,filename,protocol):
    f=open(filename, 'wb')
    # If you are awared of the compatibility issues
    # Well, you use cache only on your own computer, right?
    pickle.dump(obj,f,protocol=protocol)
    f.close()

def loadfromfile(filename):
    if(os.path.isfile(filename)):
        f=open(filename,'rb')
        obj=pickle.load(f)
        f.close()
        return obj
    else:
        raise Exception('No cache of %s'%filename)


def load(*names):
    if(len(names)==1):
        return loadfromfile(os.path.join(WORKING_PATH,'cache_data/%s.cache'%names[0]))
    result=[None]*len(names)
    for i in range(len(names)):
        result[i]=loadfromfile(os.path.join(WORKING_PATH,'cache_data/%s.cache'%names[i]))
    return result

def save(obj,name,protocol=pickle.HIGHEST_PROTOCOL):
    path=os.path.join(WORKING_PATH,'cache_data/%s.cache'%name)
    mkdir_for_file(path)
    dumptofile(obj,path,protocol)

def hasher(obj):
    if(isinstance(obj,list)):
        m=hashlib.md5()
        for item in obj:
            m.update(item)
        return m.hexdigest()
    if(isinstance(obj,str)):
        return hashlib.md5(obj.encode("utf8")).hexdigest()
    return hashlib.md5(obj).hexdigest()