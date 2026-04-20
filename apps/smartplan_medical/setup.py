from setuptools import setup, find_packages

setup(
    name="smartplan_medical",
    version="1.0.0",
    description="Progressive Web App layer for ERPNext - SmartPlan Medical",
    author="SmartPlan Solutions",
    author_email="dev@eg-smartplan.solutions",
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
)
