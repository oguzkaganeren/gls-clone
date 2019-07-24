"""
config file in user $HOME
"""

import configparser
from pathlib import Path
from collections import namedtuple

class UserConf():
    """
    File in $HOME/.config/ for save / load parameters
    To use as context manager only
    """

    KEY = 'SETTING'

    def __init__(self, app_name: str):
        """
        initialize object

        Args:
            app_name (str): name of application
        """

        self.inifile = Path.home() / f".config/{app_name}.conf"
        self.inifile.parent.mkdir(parents=True, exist_ok=True)
        self.config = None  # can use only after "with"
        self.modified = False

    def __enter__(self) -> object:
        """
        enter in "with" ...
        """

        self.config = configparser.ConfigParser()
        self.config.read(self.inifile)
        self.modified = False
        # create default session "KEY" if not exists
        try:
            self.config[self.KEY]
        except KeyError:
            self.config[self.KEY] = {}

        return self

    def __exit__(self, etype, evalue, traceback) -> None:
        self.save()

    def save(self):
        if self.modified:
            with open(self.inifile, 'wt') as configfile:
                self.config.write(configfile)

    def _safe_section_name(self, section: str) ->str:
        """
            use only uppercase

            Returns: default section if empty
        """

        if not section:
            section = self.KEY
        return section.upper()

    def write(self, fields: dict, section: str = ''):
        """
        set values in .conf

        Args:
            fields (dict): datas
            section (str, optional): section name. Default is self.KEY
        """

        section = self._safe_section_name(section)
        try:
            section_object = self.config[section]
        except KeyError:
            self.config[section] = {}
        section_object = self.config[section]

        for key, value in fields.items():
            section_object[key] = str(value)
        self.modified = True

    def reads(self, section: str = '') -> namedtuple:
        """
        load all keys section

        Returns:
            namedtuple, values converted

        Raises:
            KeyError: section not exits
        """

        section = self._safe_section_name(section)
        try:
            datas = dict(self.config.items(section))
            # convert types
            for key, value in datas.items():
                if value == "True":
                    datas[key] = True
                if value == "False":
                    datas[key] = False
                if value.isdigit():
                    datas[key] = int(value)
            return namedtuple(section, datas.keys())(*datas.values())
        except (KeyError, configparser.NoSectionError) as err:
            raise KeyError(f"Section \"{section}\" not exists") from err

    def read(self, key: str, section: str = '', boolean=False, default=None):
        """
        read a key in .conf file

        Args:
            key (str): key
            section (str, optional): section name. Default is self.KEY
            boolean (bool, optional): evaluate strings "True,False"
            default (optional): default return if key not exists

        Returns:
            [string, bool, optional]: value for key
        """

        section = self._safe_section_name(section)
        try:
            return self.config.getboolean(section, key) if boolean else self.config.get(section, key)
        except KeyError:
            return default or None



if __name__ == '__main__':

    """
    tests
    HOWTO use this library
    """

    # create file and save
    user = UserConf('TEST/OneTest')
    with user:
        user.write({'kde': 'gnome'})   # in default section
        user.write({'first': 'True'}, 'TEST')
        user.write({'x': 55, 'y':199, 'z':True}, 'SIZE')


    # add new keys and change values
    with UserConf('TEST/OneTest') as user:
        user.write({
            'want': 'yes',
            'count': 5,
            'first': False, # override first save
        }, 'TEST')
        user.write({'Demo':True}, 'TEST')

    # read after saved
    with UserConf('TEST/OneTest') as user:
        value = user.read('demo', 'TEST')
        print("value section TEST, key Demo:", value)

        if user.read('want', 'TEST', boolean=True):
            print("[TEST] want = True")

        position = user.reads('SIZE')
        print(position, type(position.x), type(position.y), type(position.z))
        print(type(position), position.x, position.y,  position.z)
        print("size:", position, position.x, position.y)

        print("section not exists ?")
        try:
            position = user.reads('POSITION')
            print(type(position))
            print("size:", position, position.x, position.y)
        except KeyError as err:
            print("opps !", str(err))


    # verif, show .ini
    print("\n--------------\n", user.inifile)   # file to remove (parent dir if not .config/)
    print("--------------\n")
    with open(user.inifile, 'r') as f_read:
        for line in f_read:
            print(line, end='')
    print("\n--------------\n")
