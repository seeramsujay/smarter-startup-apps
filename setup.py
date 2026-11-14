import os

from setuptools import find_packages, setup


def check_create_data_dir():
    data_dir = os.path.join(os.path.expanduser("~"), ".local", "share", "ghostos")
    os.makedirs(data_dir, exist_ok=True)
    os.makedirs(os.path.join(data_dir, "logs"), exist_ok=True)


try:
    check_create_data_dir()
except Exception:
    pass

setup(
    name="ghostos-x",
    version="3.0.0",
    description="Activity Intelligence Engine for Linux",
    author="Thors",
    py_modules=["ghostos", "activity_logger", "tracker"],
    packages=find_packages(),
    package_data={
        "config": ["config.json"],
    },
    include_package_data=True,
    python_requires=">=3.10",
    entry_points={
        "console_scripts": [
            "ghostos=ghostos:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
    ],
)
