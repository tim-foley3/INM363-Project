from setuptools import setup, find_packages

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

# read the contents of the README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()


setup(name='light_shaders',
      version='0.1.1',
      description='OpenGL shading for Arcade environments',
      author='Tim Foley',
      author_email='tim.foley@city.ac.uk',
      packages=find_packages(where="src"),
      package_dir={"": "src"},
      include_package_data=True,
      install_requires=requirements,
      long_description=long_description,
      long_description_content_type='text/markdown'
      )