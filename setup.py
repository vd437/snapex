from setuptools import setup, find_packages

setup(
    name="snapex",
    version="1.0.0",
    description="The Ultimate HTTP Client for Python",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="vd437",
    url="https://github.com/vd437/snapex",
    packages=find_packages(),
    install_requires=[
        "brotli",
        "websockets",
    ],
    extras_require={
        'http2': ['h2'],
        'http3': ['aioquic'],
        'full': ['h2', 'aioquic'],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.7",
)