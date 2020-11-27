#!/usr/bin/env python3
 
from setuptools import setup, find_packages
from bin import __version__

'''
https://setuptools.readthedocs.io/en/latest/setuptools.html#new-and-changed-setup-keywords
build:
python setup.py bdist
'''
setup(
    name='layoutswitcherlib',
    version=__version__,
    description='Gnome Layout Switcher',
    url='https://gitlab.manjaro.org/Chrysostomus/gnome-layout-switcher',
    download_url='https://gitlab.manjaro.org/Chrysostomus/gnome-layout-switcher',
    keywords = ["gnome", "manjaro"],
    author="Chrysostomus, papajoke, Ste74",
    
    python_requires='>=3.7',
    packages=['layoutswitcherlib'],

    package_dir = {'layoutswitcherlib' : 'bin/layoutswitcherlib'},
    include_package_data=True,
    

    data_files=[
        ('share/icons/hicolor/scalable/apps',[
            'data/gnome-layout-switcher.svg',
         ]),
        ('share/gls/pictures',[
            'data/pictures/gnomepreview.svg',
            'data/pictures/modernpreview.svg',
            'data/pictures/manjaropreview.svg',
            'data/pictures/matepreview.svg',
            'data/pictures/material_shellpreview.svg',
            'data/pictures/unitypreview.svg',
            'data/pictures/classicpreview.svg',
         ]),
        ('share/gls/schemas',[
            'data/schemas/classic_layout',
            'data/schemas/unity_layout',
         ]),
        ('share/gtk-3.0',[
            'data/css/gtk.css',
         ]),
         ('bin/',[
            'bin/gnome-layout-switcher',
         ]),
        ('share/applications',[
            'data/desktop/gnome-layouts.desktop',
         ]),

        # not used in this branch
        #('share/polkit-1/actions/',[
        #    'data/org.manjaro.org.gnomelayoutswitcher.policy',
        # ]),
     ]
    
    #install_requires = ['pygtk'],
)
