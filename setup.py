#!/usr/bin/env python3
import multiprocessing
import os
import subprocess
import sys
from pathlib import Path

import setuptools
from sphinx.setup_command import BuildDoc
from wheel.bdist_wheel import bdist_wheel


VERSION = (0, 5, 2, "post7")


def version_str(version):
    return ".".join(map(str, version))


class platform_bdist_wheel(bdist_wheel):
    """Patched bdist_well to make sure wheels include platform tag."""

    def finalize_options(self):
        bdist_wheel.finalize_options(self)
        self.root_is_pure = False


def configure_c_extension():
    """Configure cmake project to C extension."""
    print(
        f"Configuring for python {sys.version_info.major}.{sys.version_info.minor}..."
    )
    os.makedirs("cmake_build", exist_ok=True)
    cmake_command = [
        "cmake",
        "../opensfm/src",
        "-DPYTHON_EXECUTABLE=" + sys.executable,
    ]

    if sys.platform == "win32":
        cmake_command += [
            "-DVCPKG_TARGET_TRIPLET=x64-windows",
            "-DCMAKE_TOOLCHAIN_FILE=../vcpkg/scripts/buildsystems/vcpkg.cmake",
        ]
    subprocess.check_call(cmake_command, cwd="cmake_build")


def build_c_extension():
    """Compile C extension."""
    print("Compiling extension...")
    if sys.platform == "win32":
        subprocess.check_call(
            ["cmake", "--build", ".", "--config", "Release"], cwd="cmake_build"
        )
    else:
        subprocess.check_call(
            ["make", "-s", "-j" + str(multiprocessing.cpu_count())], cwd="cmake_build"
        )


configure_c_extension()
build_c_extension()
cmake_dir = Path(__file__).parent.joinpath("cmake_build")
data_files = [p.as_posix() for p in cmake_dir.glob("*.so")]

lib_folder = os.path.dirname(os.path.realpath(__file__))
requirement_path = f"{lib_folder}/requirements.txt"
install_requires = []  # Here we'll add: ["gunicorn", "docutils>=0.3", "lxml==0.5a7"]
if os.path.isfile(requirement_path):
    with open(requirement_path) as f:
        install_requires = f.read().splitlines()

setuptools.setup(
    name="opensfm",
    version=version_str(VERSION),
    description="A Structure from Motion library",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/mapillary/OpenSfM",
    project_urls={
        "Documentation": "https://docs.opensfm.org/",
    },
    author="Mapillary",
    license="BSD",
    packages=setuptools.find_packages(),
    scripts=[
        "bin/opensfm_run_all",
        "bin/opensfm",
        "bin/opensfm_main.py"
    ],
    package_data={
        "opensfm": [
            "data/sensor_data.json",
            "data/camera_calibration.yaml",
            "data/bow/bow_hahog_root_uchar_10000.npz",
            "data/bow/bow_hahog_root_uchar_64.npz",
        ]
    },
    # ext_modules=[
    #     setuptools.Extension('pybundle', ['source/OpenSfM/opensfm/src/pybundle.cpython-310-x86_64-linux-gnu.so']),
    #     setuptools.Extension('pydense', ['source/OpenSfM/opensfm/src/pydense.cpython-310-x86_64-linux-gnu.so']),
    #     setuptools.Extension('pyfeatures', ['source/OpenSfM/opensfm/src/pyfeatures.cpython-310-x86_64-linux-gnu.so']),
    #     # Add all your shared libraries here
    # ],
    data_files=[('lib', data_files)],
    cmdclass={
        "bdist_wheel": platform_bdist_wheel,
        "build_doc": BuildDoc,
    },
    command_options={
        "build_doc": {
            "project": ("setup.py", "OpenSfM"),
            "version": ("setup.py", version_str(VERSION[:2])),
            "release": ("setup.py", version_str(VERSION)),
            "source_dir": ("setup.py", "doc/source"),
            "build_dir": ("setup.py", "build/doc"),
        }
    },
    install_requires=install_requires,
)