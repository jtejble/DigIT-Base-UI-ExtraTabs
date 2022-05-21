import json, os, glob, copy
from . import app

import torch

class Settings:
    FILENAME = 'settings.json'   #FIXME: hardcoded

    def __init__(self):
        self.models        = dict()  #python objects
        self.active_models = dict()  #modelnames
        self.set_settings( self.load_settings_from_file(), save=False )

    @classmethod
    def get_defaults(cls):
        available_models = cls.get_available_models()
        first_or_none    = lambda x: x[0] if len(x) else None
        return dict( active_models = dict([
            (modeltype, first_or_none(models)) for modeltype, models in available_models.items()
        ] ) )

    def load_settings_from_file(self):
        s = self.get_defaults()
        if os.path.exists(self.FILENAME):
            s.update(json.load(open(self.FILENAME)))
            #self.set_settings(s)
        else:
            print(f'[WARNING] Settings file {self.FILENAME} not found.')
            #self.set_settings(s, save=False)
        return s

    def set_settings(self, s, save=True):
        print('Settings: ', s)
        for modeltype, modelname in s.get('active_models', {}).items():
            if self.active_models.get(modeltype, None) != modelname:
                self.models[modeltype] = self.load_model(modeltype, modelname)
        self.__dict__.update( copy.deepcopy(s) )

        if save:
            previous_s = self.load_settings_from_file()
            for modeltype, modelname in s['active_models'].items():
                if modelname == '':  #unsaved
                    s['active_models'][modeltype] = previous_s['active_models'].get(modeltype)
            json.dump( s, open('settings.json','w'), indent=2) 

    def get_settings_as_dict(self):
        #s = self.load_settings_from_file()
        s = self.get_defaults()
        s = dict([ (k,getattr(self,k,v)) for k,v in s.items() ])
        return {
            'settings'         : s,
            'available_models' : self.get_available_models()
        }

    @staticmethod
    def get_available_models():
        modelsdir  = app.get_models_path()
        contents   = glob.glob(os.path.join(modelsdir, '*'))
        modeltypes = [os.path.basename(x) for x in contents if os.path.isdir(x)]
        models     = dict()
        for modeltype in modeltypes:
            modelfiles = glob.glob(os.path.join(modelsdir, modeltype, '*.pt.zip'))
            modelnames = [os.path.basename(m)[:-len('.pt.zip')] for m in modelfiles]
            modelfiles = glob.glob(os.path.join(modelsdir, modeltype, '*.pkl'))       #TODO: remove pkl files
            modelnames += [os.path.basename(m)[:-len('.pkl')] for m in modelfiles]
            models[modeltype] = modelnames
        return models

    @staticmethod
    def load_model(modeltype, modelname):
        import pickle
        print(f'Loading model {modeltype}/{modelname}')
        path  = os.path.join(app.get_models_path(), modeltype, f'{modelname}.pt.zip')
        if os.path.exists(path):
            model = torch.package.PackageImporter(path).load_pickle('model', 'model.pkl')
            return model
        else:
            path  = os.path.join(app.get_models_path(), modeltype, f'{modelname}.pkl')
            if not os.path.exists(path):
                print(f'[ERROR] model file "{path}" does not exist.')
                return
            model = pickle.load(open(path, 'rb'))
            return model

