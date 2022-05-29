from setuptools import setup, find_packages

setup(name='notesaladtools',
      version='0.2',
      packages=find_packages(),
      install_requires=[],
      entry_points={
          'console_scripts': [
              'nsdump=notesaladtools.nsdump:main',
              'nsplay=notesaladtools.nsplay:main',
              'nsconvert=notesaladtools.nsconvert:main',
              'nsmidi=notesaladtools.nsmidi:main'
          ]
      }
      )
