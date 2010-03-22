from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages, Extension, Library
import glob
import platform

                  
#INSTALL or offer to install non-easy_install software

#eyeD3 is necessary for working with mp3s #todo use TagLib some day
try :
    import eyeD3
except :
    print 'WARNING: You will need eyeD3 to read and write mp3 ID3 tags'
    print ' - Please install eyeD3 (cd ./eyeD3; ./configure; make; make install)'
    print ' - If you need to install to nonstandard location use the --prefix flag for configure'
    print ' - That is: ./configure --prefix=<the root of where you want to install the software'





#todo add dependacy for pypdf



setup(name="Gordon",
      version="0.1",
      author="Douglas Eck and others",
      author_email="douglas.eck@gmail.com",
      description="Gordon Music Management System",
      license="GNU GPL",
      #keywords="music information retrieval, music database",
      #url="bitbucket.com/gordon",
      packages=find_packages(exclude='tests'),
      long_description="""This is the Gordon Music Management System.""",
      #classifiers=["Development Status :: 3 - Alpha",
                    ]
      test_suite = "nose.collector",     
      scripts=[ 'gordon/db/audio_intake.py',
                'gordon/db/mbrainz_import.py',
                'gordon/db/mbrainz_resolver.py',
                'gordon/db/playdar_resolver.py',
                ],
      install_requires=[],
)
