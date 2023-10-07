from setuptools import setup

setup(name="clean_folder",
      version="0.0.1",
      licence="MIT",
      entry_points={"console_scripts": ["clean-folder = clean_folder.clean:main"]})