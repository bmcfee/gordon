#from ez_setup import use_setuptools
#use_setuptools()
from setuptools import setup, find_packages#, Extension, Library
#import glob
#import platform

try :
    import eyeD3 #todo: change this if tagpy is employed instead
except :
    print 'WARNING: You will need eyeD3 to read and write mp3 ID3 tags'
    print ' - Please install eyeD3 (cd ./eyeD3; ./configure; make; make install)'
    print ' - If you need to install to nonstandard location use the --prefix flag for configure'
    print ' - That is: ./configure --prefix=<the root of where you want to install the software'

#todo: add all dependencies

setup(name="Gordon",
      version="0.5",
      author="Douglas Eck, Ron Weiss, Jorge Orpinel",
      author_email="douglas.eck@gmail.com",
      description="Gordon Music Management System",
      license="GNU GPL",
      #keywords="music information retrieval, music database",
      url="bitbucket.org/ronw/gordon",
      packages=find_packages(exclude='tests'),
      long_description="""This is the Gordon Music Management System.""",
      #classifiers=["Development Status :: 3 - Alpha",
      #              ],
      test_suite = "nose.collector",
      scripts=[ 'scripts/audio_intake_from_tracklist.py',
                'scripts/audio_intake.py',
                'scripts/generate_tracklist_from_regexp.py',
                'scripts/generate_tracklist_from_tags.py',
                'scripts/gordon_initialize.py',
                'scripts/mbrainz_import.py',
                'scripts/mbrainz_resolver.py',
                ],
      install_requires=[],
)
