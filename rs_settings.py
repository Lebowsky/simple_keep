import json
import os

class RSSettings():

    def __init__(self):

       # self._filename = '//data/data/ru.travelfood.simple_ui/rs_settings.conf'
        self._filename = 'rs_settings.conf' #//storage/emulated/0/download/

        if os.path.exists(self._filename):
            with open(self._filename, 'r') as infile:
                self.data = json.load(infile)
        else:
            self.data = {}

    @staticmethod
    def get(parameter_name):
        settings = RSSettings()
        if parameter_name in settings.data:
            return str(settings.data[parameter_name])
        else:
            return 'not found'
            # raise KeyError(f"Parameter '{parameter_name}' not found in JSON file")

    @staticmethod
    def put(parameter_name, value, NoNeed = True):
        self = RSSettings()
        self.data[parameter_name] = value
        if os.path.exists(self._filename):
            with open(self._filename, 'w') as outfile:
                json.dump(self.data, outfile)
        else:
            try:
                with open(self._filename, 'x') as outfile:
                    json.dump(self.data, outfile)
            except: raise ConnectionRefusedError('Нет доступа к файлу')

    @staticmethod
    def get_all():
        self = RSSettings()

        return (self.data)
