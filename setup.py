from setuptools import find_packages, setup

import djangocms_references


INSTALL_REQUIREMENTS = [
    "Django>=1.11,<3.0",
    "django-cms"
]


setup(
    name="djangocms-references",
    packages=find_packages(),
    include_package_data=True,
    version=djangocms_references.__version__,
    description=djangocms_references.__doc__,
    long_description=open("README.rst").read(),
    classifiers=[
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Software Development",
    ],
    install_requires=INSTALL_REQUIREMENTS,
    author="Fidelity International",
    url="https://github.com/fidelityInternational/djangocms-references",
    license="BSD",
    test_suite="tests.settings.run",
    dependency_links=[
        "http://github.com/divio/django-cms/tarball/release/4.0.x#egg=django-cms-4.0.0",
    ]
)
