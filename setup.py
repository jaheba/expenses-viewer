
from setuptools import setup


setup(
    name='expense-viewer',
    version='0.2',
    packages=['exp_viewer'],
    install_requires=[
        'flask',
        'lxml',
        'frozen-flask',
        'click',
    ],
    entry_points={
        'console_scripts': [
            'expenses-viewer=exp_viewer.app:main',
            'sd-cli=exp_viewer.cli:cli',
        ]
    },
    include_package_data = True,

)
