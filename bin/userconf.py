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

    def write(self, fields: dict, title: str = ''):
        """
        set values in .conf

        Args:
            fields (dict): datas
            title (str, optional): section name. Default is self.KEY
        """

        if not title:
            title = self.KEY
        title = title.upper()
        try:
            section = self.config[title]
        except KeyError:
            self.config[title] = {}
        section = self.config[title]

        for key, value in fields.items():
            section[key] = str(value)
        self.modified = True

    def reads(self, title: str = '') -> namedtuple:
        """
        load all keys section
        """
        if not title:
            title = self.KEY
        title = title.upper()
        try:
            datas = dict(self.config.items(title))
            return namedtuple(title, datas.keys())(*datas.values())
        except (KeyError, configparser.NoSectionError) as err:
            raise KeyError(f"Section \"{title}\" not exists") from err

    def read(self, key: str, title: str = '', boolean=False, default=None):
        """
        read a key in .conf file

        Args:
            key (str): key
            title (str, optional): section name. Default is self.KEY
            boolean (bool, optional): evaluate strings "True,False"
            default (optional): default return if key not exists

        Returns:
            [string, bool, optional]: value for key
        """

        if not title:
            title = self.KEY
        title = title.upper()
        try:
            return self.config.getboolean(title, key) if boolean else self.config.get(title, key)
        except KeyError:
            return default or None


class WinConf(UserConf):
    def write_pos(self):
        pass


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
        user.write({'x': 55, 'y':199}, 'SIZE')


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
        print(type(position))
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
