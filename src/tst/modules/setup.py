# setup.py - Archivo de configuración para la instalación del proyecto.
# Desarrollado por Héctor F. Rivera Santiago
# Copyright (c) 2024
# Proyecto: Smart Recycling Bin

from setuptools import setup, find_packages

setup(
    name="smart_recycling_bin",
    version="1.0.0",
    description="Sistema modular para Raspberry Pi con soporte para AWS IoT y sensores espectroscópicos.",
    author="Héctor F. Rivera Santiago",
    author_email="hector.rivera@example.com",
    url="https://github.com/tu_proyecto/smart_recycling_bin",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "paho-mqtt>=1.6.1",
        "pyyaml>=6.0",
        "boto3>=1.28.0",
    ],
    python_requires=">=3.7",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        "console_scripts": [
            "start-pi1=main_pi1:main",
            "start-pi2=main_pi2:main",
            "start-pi3=main_pi3:main",
        ],
    },
)
