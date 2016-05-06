
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
        'console_scripts': 'expenses-viewer=exp_viewer.app:main'
    },
)
