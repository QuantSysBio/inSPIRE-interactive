from setuptools import setup

setup(
    name='inspire-interact',
    version=1.0,
    description='Interactive GUI for inSPIRE Platform.',
    author='John Cormican, Juliane Liepe, Manuel S. Pereira',
    author_email='juliane.liepe@mpinat.mpg.de',
    packages=[
        'inspire_interact',
    ],
    long_description=open('README.md', mode='r', encoding='UTF-8').read(),
    long_description_content_type='text/markdown',
    py_modules=[
        'inspire_interact',
    ],
    entry_points={
        'console_scripts': [
            'inspire-interact=inspire_interact.api:main'
        ]
    },
    python_requires='>=3.8',
    install_requires=[
        #'inspirems',
    ],
    project_urls={
        'Homepage': 'https://github.com/QuantSysBio/inSPIRE',
        'Tracker': 'https://github.com/QuantSysBio/inSPIRE/issues',
    },
)