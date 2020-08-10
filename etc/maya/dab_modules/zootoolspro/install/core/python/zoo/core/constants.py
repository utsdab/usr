# Environment variable that sets the location of the config folder
ZOO_CFG_PATH_ENV = "ZOO_CONFIG_PATH"
# Environment variable that sets the installed packages location.
ZOO_PKG_PATH_ENV = "ZOO_PACKAGES_PATH"
# package environment json environment variable
ZOO_PKG_VERSION_PATH = "ZOO_PACKAGE_VERSION_PATH"
# Config folder name.
CONFIG_FOLDER_NAME = "config"
# Packages folder name.
PKG_FOLDER_NAME = "packages"
# Environment variable which defines the location of CLI commands.
COMMANDLIBRARY_ENV = "ZOO_CMD_PATH"
# file names to exclude when
FILE_FILTER_EXCLUDE = (".gitignore", ".gitmodules", ".flake8.ini",
                       ".hound.yml", "setup.py", "docs", "*.git", "*.vscode", "*__pycache__",
                       "*.idea", "MANIFEST.ini")
# config token which can be used in descriptor paths
# this will be converted to the abspath
CONFIG_FOLDER_TOKEN = "{config}"
# package folder token for descriptors
# resolves to each package root
PKG_FOLDER_TOKEN = "{self}"
# per package file name
PACKAGE_NAME = "zoo_package.json"
DEPENDENT_FILTER = r"\{(.*?)\}"

CLI_ROOT_NAME = "Zootools CLI"
ZOO_ADMIN = "ZOO_ADMIN"