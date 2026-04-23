from setuptools import setup, find_packages

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="spikesorting-labhub",
    packages=find_packages(),
    version="0.1.0",
    author="rth",
    author_email="rath@gwu.edu",
    description="A distributed spikesorting LabHub web application",
    url="https://github.com/UserFriendlySpikesorting/SpikesortingLabHub",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GPL 3",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.10",
    install_requires=requirements,
)