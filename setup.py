from setuptools import setup, find_packages

setup(
    name="merval-fundamentals",
    version="1.0.0",
    description="Análisis fundamental automático del panel líder Merval",
    author="GuillermoSiaira",
    url="https://github.com/GuillermoSiaira/merval-fundamentals",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "anthropic>=0.42.0",
        "google-cloud-firestore>=2.16.0",
        "google-cloud-logging>=3.11.1",
        "requests>=2.32.0",
        "python-dotenv>=1.0.0",
        "pandas>=2.2.0",
        "pytz>=2024.1",
    ],
)
