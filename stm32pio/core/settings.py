"""
This file provides all kinds of configurable parameters for different application modules. Also, this is a source of the
default project config file stm32pio.ini.

Bottom part of the file contains some definitions specifically targeting continuous integration environment. They have
no effect on normal or test (local) runs.
"""

import inspect
import logging
import os
import platform
from pathlib import Path


my_os = platform.system()

config_file_name = 'stm32pio.ini'

config_default = dict(
    # "app" section is used for listing commands/paths of utilized programs
    app={
        # How do you start the PlatformIO from command line?
        #  - If you're using PlatformIO IDE see
        #    https://docs.platformio.org/en/latest/core/installation.html#piocore-install-shell-commands
        #  - If you're using PlatformIO CLI but it is not available as 'platformio' command, add it to your PATH
        #    environment variable (refer to OS docs)
        #  - Or simply specify here a full path to the PlatformIO executable
        # Note: "python -m platformio" isn't supported yet
        'platformio_cmd': 'platformio',

        # STM32CubeMX doesn't register itself in PATH so we specify a full path to it. Here are default ones (i.e. when
        # you've installed CubeMX on your system)
        'cubemx_cmd':
            # macOS default: 'Applications' folder
            '/Applications/STMicroelectronics/STM32CubeMX.app/Contents/MacOs/STM32CubeMX' if my_os == 'Darwin' else
            # Linux (at least Ubuntu) default: home directory
            str(Path.home() / 'STM32CubeMX/STM32CubeMX') if my_os == 'Linux' else
            # Windows default: Program Files
            'C:/Program Files/STMicroelectronics/STM32Cube/STM32CubeMX/STM32CubeMX.exe' if my_os == 'Windows' else '',

        # If you're on Windows or you have CubeMX version below 6.3.0, the Java command (which CubeMX is written on)
        # should be specified. For CubeMX starting from 6.3.0 JRE is bundled alongside, otherwise it must be installed
        # by a user yourself separately
        'java_cmd':
            'C:/Program Files/STMicroelectronics/STM32Cube/STM32CubeMX/jre/bin/java.exe'
            if my_os == 'Windows' else 'None',
    },

    # "project" section focuses on parameters of the concrete stm32pio project
    project={
        # CubeMX can be fed with the script file to read commands from. This template is based on official user manual
        # PDF (UM1718)
        'cubemx_script_content': inspect.cleandoc('''
            config load ${ioc_file_absolute_path}
            generate code ${project_dir_absolute_path}
            exit
        '''),

        # In order for PlatformIO to "understand" a code generated by CubeMX, some tweaks (both in project structure and
        # config files) should be applied. One of them is to inject some properties into the platformio.ini file and
        # this option is a config-like string that should be merged with it. In other words, it should meet INI-style
        # requirements and be a valid platformio.ini config itself
        'platformio_ini_patch_content': inspect.cleandoc('''
            [platformio]
            include_dir = Inc
            src_dir = Src
        '''),

        'board': '',  # one of PlatformIO boards identifiers (e.g. "nucleo_f031k6")

        # CubeMX .ioc project config file. Typically, this will be filled in automatically on project initialization
        'ioc_file': '',

        'cleanup_ignore': '',
        'cleanup_use_git': False,  # controls what method 'clean' command should use

        'inspect_ioc': True
    }
)

# Values to match with on user input (both config and CLI) (use in conjunction with .lower() to ignore case)
none_options = ['none', 'no', 'null', '0']
no_options = ['n', 'no', 'false', '0']
yes_options = ['y', 'yes', 'true', '1']

# CubeMX 0 return code doesn't necessarily mean a successful operation (e.g. migration dialog has appeared and 'Cancel'
# was chosen, or CubeMX_version < ioc_file_version, etc.), we should analyze the actual output (STDOUT)
# noinspection SpellCheckingInspection
cubemx_str_indicating_success = 'Code succesfully generated'
cubemx_str_indicating_error = 'Exception in code generation'  # final line "KO" is also a good sign of error

# Longest name (not necessarily a method so a little bit tricky...)
# log_fieldwidth_function = max([len(member) for member in dir(stm32pio.lib.Stm32pio)]) + 1
log_fieldwidth_function = 20  # TODO: ugly and not so reliable anymore...

show_traceback_threshold_level = logging.DEBUG  # when log some error and need to print a traceback

pio_boards_cache_lifetime = 5.0  # in seconds


#
# Do not distract end-user with this CI s**t, take out from the main dict definition above
#
# TODO: Probably should remove those CI-specific logic from the source code entirely. This problem is related to having
#  an [optional] single (global) config
# Environment variable indicating we are running on a CI server and should tweak some parameters
CI_ENV_VARIABLE = os.environ.get('PIPELINE_WORKSPACE')
if CI_ENV_VARIABLE is not None:
    # TODO: Python 3.8+: some PyCharm static analyzer bug. Probably can be solved after introduction of TypedDict
    # noinspection PyTypedDict
    config_default['app'] = {
        'platformio_cmd': 'platformio',
        'cubemx_cmd': str(Path(os.environ.get('STM32PIO_CUBEMX_CACHE_FOLDER')) / 'STM32CubeMX.exe'),
        'java_cmd': 'java'
    }

    TEST_FIXTURES_PATH = Path(os.environ.get('STM32PIO_TEST_FIXTURES',
                                             default=Path(__file__).parent / '../../tests/fixtures'))
    TEST_CASE = os.environ.get('STM32PIO_TEST_CASE')
    patch_mixin = ''
    if TEST_FIXTURES_PATH is not None and TEST_CASE is not None:
        platformio_ini_lockfile = TEST_FIXTURES_PATH / TEST_CASE / 'platformio.ini.lockfile'
        if platformio_ini_lockfile.exists():
            patch_mixin = '\n\n' + platformio_ini_lockfile.read_text()
    config_default['project']['platformio_ini_patch_content'] += patch_mixin
