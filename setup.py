from setuptools import setup
__version__ = '1.4'

from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description=f.read()


setup(
  name = 'proc_plot',
  packages = ['proc_plot'],
  version = __version__,
  license='GPLv3', 
  description = 'Trending for Process Control Data Analysis',
  long_description=long_description,
  long_description_content_type='text/markdown',
  author = 'Francois Pieterse',
  author_email = 'francois.pieterse@greenferndynamics.com',
  url = 'https://github.com/fpieterse/proc_plot',
  download_url = 'https://github.com/fpieterse/proc_plot/archive/v'+__version__+'.tar.gz',
  keywords = ['Trend','Process Control'],
  install_requires=[
          'pandas',
          'matplotlib',
          'pyperclip'
      ],
  classifiers=[
    'Development Status :: 5 - Production/Stable',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Manufacturing',      # Define that your audience are developers
    'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
    'Programming Language :: Python :: 3',      #Specify which pyhton versions that you want to support
    'Programming Language :: Python :: 3.6',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
  ],
)
