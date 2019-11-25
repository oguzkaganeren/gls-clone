#!/usr/bin/env python3
 
from setuptools import setup, find_packages

'''
https://setuptools.readthedocs.io/en/latest/setuptools.html#new-and-changed-setup-keywords
build:
python setup.py bdist
'''

setup(
    name='layoutswitcherlib',
    version='0.6.1',
    description='Gnome Layaouts Switcher',
    url='https://gitlab.manjaro.org/Chrysostomus/gnome-layout-switcher',
    download_url='https://gitlab.manjaro.org/Chrysostomus/gnome-layout-switcher',
    keywords = ["gnome", "manjaro"],
    
    python_requires='>=3.7',
    packages=['layoutswitcherlib'],

    package_dir = {'layoutswitcherlib' : 'bin/layoutswitcherlib'},
    include_package_data=True,
    

    data_files=[
        ('share/icons/hicolor/scalable/apps',[
            'data/gnome-layout-switcher.svg',
         ]),
        ('share/gls',[
            'data/pictures/gnomepreview.svg',
            'data/pictures/macpreview.svg',
            'data/pictures/manjaropreview.svg',
            'data/pictures/winpreview.svg',
         ]),
        ('share/gtk-3.0',[
            'data/css/gtk.css',
         ]),
        # not used in this branch
        #('share/polkit-1/actions/',[
        #    'data/org.manjaro.org.gnomelayoutswitcher.policy',
        # ]),
     ]
    
    #install_requires = ['pygtk'],
)
