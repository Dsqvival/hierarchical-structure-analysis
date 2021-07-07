import os
from mir.settings import *

WORKING_PATH=os.getcwd()
PACKAGE_PATH=os.path.dirname(os.path.abspath(__file__))

DEFAULT_DATA_STORAGE_PATH=DEFAULT_DATA_STORAGE_PATH.replace('$project_name$',os.path.basename(os.getcwd()))
