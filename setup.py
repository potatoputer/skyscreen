"""py2app setup script for SkyScreen."""
from setuptools import setup

APP = ['monitor_position.py']
DATA_FILES = []
OPTIONS = {
    'argv_emulation': False,
    'iconfile': None,
    'plist': {
        'CFBundleName': 'SkyScreen',
        'CFBundleDisplayName': 'SkyScreen',
        'CFBundleIdentifier': 'com.skyscreen.app',
        'CFBundleVersion': '1.1.0',
        'CFBundleShortVersionString': '1.1.0',
        'LSUIElement': True,
        'NSHighResolutionCapable': True,
    },
    'packages': ['rumps', 'pynput', 'PIL'],
    'includes': [
        'threading',
        'time',
        'tempfile',
        'os',
        'Quartz',
        'AppKit',
    ],
    'excludes': [
        'tkinter',
        'Tkinter',
        '_tkinter',
        'matplotlib',
        'numpy',
        'scipy',
        'pandas',
        'IPython',
        'PyQt5',
        'PyQt6',
        'wx',
    ],
}

setup(
    name='SkyScreen',
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
