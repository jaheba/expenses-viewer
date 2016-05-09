
from setuptools import setup


setup(
    name='expense-viewer',
    version='0.1',
    packages=['exp_viewer'],
    install_requires=[
        'flask',
        'lxml',
    ],
    entry_points={
        'console_scripts': [
            'expenses-viewer=exp_viewer.app:main',
            'sd-cli=exp_viewer.cli:cli',
        ]
    },
    include_package_data = True,

)
