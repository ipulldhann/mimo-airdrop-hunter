from setuptools import setup, find_packages

setup(
    name="mimo-airdrop-hunter",
    version="0.1.0",
    description="Web3 airdrop eligibility scanner with MiMo AI",
    author="ipulldhann",
    python_requires=">=3.10",
    packages=find_packages(),
    install_requires=[
        "web3>=6.0.0",
        "openai>=1.0.0",
        "click>=8.0.0",
        "pyyaml>=6.0",
        "requests>=2.31.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "airdrop-hunter=airdrop_hunter.__main__:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Office/Business :: Financial",
        "Programming Language :: Python :: 3",
    ],
)
