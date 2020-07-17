from setuptools import setup


setup(
    app=['gui.py'],
    name='ereader-bookmark-extractor',
    data_files=[],
    options={'py2app': {}},
    setup_requires=['py2app']
)
