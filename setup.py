from setuptools import find_packages, setup


package_name = "marble_ros_common"


setup(
    name=package_name,
    version="0.1.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            [f"resource/{package_name}"],
        ),
        (f"share/{package_name}", ["package.xml"]),
    ],
    install_requires=["setuptools"],
    zip_safe=True,
    maintainer="luka",
    maintainer_email="luka.mandic@fer.hr",
    description="Shared ROS 2 launch helpers for MARBLE vehicles.",
    license="Apache-2.0",
)
