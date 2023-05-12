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
    python_requires='==3.11',
    install_requires=[
        #'inspirems==2.0',
        'Werkzeug==2.3.4',
        'blinker==1.6.2',
        'click==8.1.3',
        'flask==2.3.2',
        'flask_cors==3.0.10',
        'itsdangerous==2.1.2',
    ],
    project_urls={
        'Homepage': 'https://github.com/QuantSysBio/inSPIRE',
        'Tracker': 'https://github.com/QuantSysBio/inSPIRE/issues',
    },
)