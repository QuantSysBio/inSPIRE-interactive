from setuptools import setup, find_packages

setup(
    name='inspire-interact',
    version='0.4',
    description='Interactive GUI for inSPIRE Platform.',
    author='John Cormican, Sahil Khan, Juliane Liepe, Manuel S. Pereira',
    author_email='juliane.liepe@mpinat.mpg.de',
    include_package_data=True,
    long_description=open('README.md', mode='r', encoding='UTF-8').read(),
    long_description_content_type='text/markdown',
    py_modules=[
        'inspire_interact',
    ],
    entry_points={
        'console_scripts': [
            'inspire-interact=inspire_interact.api:main',
        ]
    },
    packages=find_packages(),
    python_requires='>=3.11',
    install_requires=[
        'inspirems==2.0rc5',
        'blinker==1.6.2',
        'click==8.1.3',
        'flask==2.3.2',
        'flask_cors==3.0.10',
        'itsdangerous==2.1.2',
        'psutil==5.9.6',
        'Werkzeug==3.0.1',
    ],
    project_urls={
        'Homepage': 'https://github.com/QuantSysBio/inSPIRE',
        'Tracker': 'https://github.com/QuantSysBio/inSPIRE/issues',
    },
    zip_safe=False,
)
