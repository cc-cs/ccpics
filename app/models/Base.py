import os

from flask import json

class app(object):
    config = {'DATA_PATH': '/Users/ujjwal/Desktop/Ujjwal/work/ccpics/data'}

class Query(object):
    '''Provides querying operations on the associated model.'''
    
    def __init__(self, model):
        self.model = model
        
    def ids(self):
        instance_ids = [f[:-4] for f in os.listdir(self.model.DATA_DIR) if f.endswith('.txt')]
        return instance_ids if instance_ids else [0]

    def data_files(self):
        files = os.listdir(self.model.DATA_DIR)
        files = [os.path.join(self.model.DATA_DIR, f) for f in files]

        return [f for f in files if os.path.isfile(f)]

    def all(self):
        instance_files = self.data_files()
        instances = []
        for instance_file in instance_files:
            with open(instance_file, 'r') as f:
                instances.append(json.load(f))

        return instances

    def get(self, instance_id):
        instance_file = os.path.join(self.model.DATA_DIR, '{}.txt'.format(instance_id))
        with open(instance_file, 'r') as f:
            instance = json.load(f)

        return instance
        
    def select(self, **criteria):
        self.model.validate_fields(criteria)

        all_instances = self.all()
        relevant_instances = []

        for instance in all_instances:
            for k, v in criteria.items():
                if instance[k] != v:
                    break # instance doesn't fit select criteria
            else: # no break, i.e., instance fits selection criteria
                relevant_instances.append(instance)

        return relevant_instances
        
    def first(self):
        return self.all()[0]

    def last(self):
        return self.all()[-1]

class ModelError(Exception):
    pass
        
class ModelMetaClass(type):
    '''
    MetaClass for all models.
    Hooks into Model class definitions to set the desired behavior for fields.
    '''

    def __new__(mcs, clsname, bases, attrs):
        '''Process the class definition to hook up handling accordingly and return the instance.'''

        if clsname == 'Model':
            return super().__new__(mcs, clsname, bases, attrs)

        # Pull the schema of Model from the class definition
        # TODO: Checking for dunder to get rid of builtin attrs is just hilarious.
        #       Find some better way to figure out user provided attributes only.
        attr_items = attrs.items()
        schema = {k.lower(): v for k, v in attr_items if '__' not in k}
        # attrs = dict(attr_items - schema.items()) # What's wrong here??? Works in idle.
        attrs = {k: v for k, v in attr_items if k.lower() not in schema}
        attrs['SCHEMA'] = schema
        attrs['FIELDS'] = {k for k in schema}
        attrs['DATA_DIR'] = os.path.join(app.config['DATA_PATH'], clsname)

        if not os.path.isdir(attrs['DATA_DIR']):
            try:
                os.makedirs(attrs['DATA_DIR'], exist_ok=False)
            except OSError:
                print("Model {} already has a data directory!".format(clsname))
                
        # Set the class dict to contain the following field buckets as class variables
        # Is this better done in the Model class?? But that'd cloud the attrs above.
        field_buckets = set(['REQUIRED', 'FOREIGN', 'UNIQUE', 'PUBLIC', 'HIDDEN', 'INDEXED'])
        for bucket in field_buckets:
            attrs[bucket] = set()

        # Go through the fields in the Model definition
        # and add them to the various field processing buckets as provided
        primary_key_not_found = True
        for field, description in schema.items():
            description = {d.upper() for d in description}
            if 'PRIMARY' in description:
                if primary_key_not_found:
                    attrs['PRIMARY_KEY'] = field
                    primary_key_not_found = False
                    description.remove('PRIMARY')
                else:
                    raise ModelError("Multiple primary keys provided.")
                
            for d in description:
                attrs[d].add(field)
                
        if primary_key_not_found:
            raise ModelError("No primary key provided.")
        
        return super().__new__(mcs, clsname, bases, attrs)

    def __init__(cls, *args, **kwargs):
        super().__init__(*args, **kwargs)
        cls.query = Query(cls)

class Model(object, metaclass=ModelMetaClass):
    '''Provide utilities for querying a model.'''

    @classmethod
    def validate_fields(cls, data):
        invalid_data_keys = data.keys() - cls.FIELDS
        if invalid_data_keys:
            raise ModelError("Invalid attributes provided: {}".format(', '.join(invalid_data_keys)))

    @classmethod
    def validate_presence(cls, data):
        missing_required_fields = cls.REQUIRED - data.keys()
        if not data or missing_required_fields:
            raise ModelError("Required attributes not present: {}".format(', '.join(missing_required_fields)))

        for k in cls.REQUIRED:
            if not data[k]:
                raise ModelError("{} is required.".format(k.title()))

    @classmethod
    def validate_uniqueness(cls, data):
        peers = cls.query.all()
        
    def __init__(self, **data):
        data = {k.lower(): v for k, v in data.items()}
        self.validate_fields(data)
        
        if not 'id' in data:
            data['id'] = int(max(self.__class__.query.ids())) + 1
            
        self.validate_presence(data)
        
        for k, v in data.items():
            self.__dict__[k] = v

    def __repr__(self):        
        return '{} : {}'.format(self.__class__.__name__, self.__dict__)
    
class Group(Model):
    id = {'primary', 'required', 'unique'}
    groupname = {'required', 'unique'}

class User(Model):
    group_id = {'required', 'unique', 'foreign'}
    id = {'primary', 'required', 'unique'}
    username = {'required', 'unique'}
    email = {'required', 'unique'}
    password = {'required', 'hidden'}

class Question(Model):
    id = {'primary', 'required', 'unique'}
    title = {'required'}
    languages = {'required'}
    body = {'required'}
    test_cases = {'required'}
    timeout = {'required'}


if __name__ == '__main__':
    rfrapp = User(group_id=1, id=1, username='rfrapp', email='rfrapp@gmail.com', password='password')
    print(rfrapp)
    
