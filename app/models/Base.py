import os

from flask import json

def user_attrs(cls):
    class dummy(object):
        pass
    
    return {k: v for k, v in vars(cls).items() if k not in vars(dummy)}

class app(object):
    config = {'DATA_PATH': '/Users/ujjwal/Desktop/Ujjwal/work/ccpics/data'}

class ModelError(Exception):
    pass
        
class ModelMetaClass(type):
    '''
    MetaClass for all models.
    Hooks into Model class definitions to set the desired behavior for fields.
    '''

    def __new__(mcs, name, bases, attrs):
        '''Process the class definition to hook up handling accordingly and return the instance.'''
        if name == 'Model':
            return super().__new__(mcs, name, bases, attrs)

        # Copy the descriptions of fields provided by the Model definition
        # TODO: Checking for dunder to get rid of builtin attrs is just hilarious.
        # Find some better way to figure out user provided attributes only.
        attr_items = attrs.items()
        field_descriptions = {k: v for k, v in attr_items if '__' not in k}
        attrs = {k: v for k, v in attr_items if k not in field_descriptions}

        # Set the class dict to contain the following field buckets as class variables
        # Is this better done in the Model class?? But that'd cloud the attrs above.
        attrs = {**attrs, 'REQUIRED': set(), 'UNIQUE': set(), 'PUBLIC': set(), 'HIDDEN': set()}

        # Go through the fields in the Model definition
        # and add them to the various field processing buckets as provided
        primary_key_not_found = True
        for field, description in field_descriptions.items():
            description = {d.upper() for d in description}
            if 'PRIMARY' in description:
                attrs['PRIMARY_KEY'] = field
                primary_key_not_found = False
                description.remove('PRIMARY')

            for d in description:
                attrs[d].add(field)
                
        if primary_key_not_found:
            raise ModelError("No primary key provided.")
        
        attrs['DATA_DIR'] = os.path.join(app.config['DATA_PATH'], name)
        return super().__new__(mcs, name, bases, attrs)

class Model(object, metaclass=ModelMetaClass):
    '''Provide utilities for querying a model.'''

    def __init__(self, **kwargs):
        pass

    @classmethod
    def fetch_ids(cls):
        '''Return all the submission ids we have so far.'''

        return [f for f in os.listdir(cls.DATA_DIR) if f.endswith('.txt')]

    def fetch_max_id():
        pass

    def __repr__(self):        
        return '{} : {}'.format(self.__class__.__name__, user_attrs(self))
    
class User(Model):
    id = {'primary', 'required', 'unique'}
    username = {'required', 'unique'}
    email = {'required', 'unique'}
    password = {'required', 'hidden'}

if __name__ == '__main__':
    print(User())
    
