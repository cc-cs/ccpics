import os

from flask import json

class app(object):
    config = {'DATA_PATH': '/Users/ujjwal/Desktop/Ujjwal/work/ccpics/data'}
        
class ModelMetaClass(type):
    '''MetaClass for all models.
    Provides functionality to set data directories and such.
    '''

    def __new__(mcs, name, bases, attrs):
        attrs['DATA_DIR'] = os.path.join(app.config['DATA_PATH'], name)
        return super().__new__(mcs, name, bases, attrs)

class BaseModel(object, metaclass=ModelMetaClass):
    
    def __init__(self, **args):
        pass

    @classmethod
    def fetch_ids(cls):
        '''Return all the submission ids we have so far.'''

        return [f for f in os.listdir(cls.DATA_DIR) if f.endswith('.txt')]

    def fetch_max_id():
        pass

class User(BaseModel):
    pass

if __name__ == '__main__':
    print(User.fetch_ids())
    
