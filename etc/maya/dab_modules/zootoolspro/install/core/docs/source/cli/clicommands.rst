
CLI Commands
####################################################

In Zootools we have have a CLI interface which allows
you to manage internal and external packages.

Before we begin playing around make sure you have
a copy of zootools in a development location eg. documents/zootoolspro.

Commands documentation

.. toctree::

    ./commands

CLI
===

You should cd into the root folder of zootools.
This is required due to the cli using the working directly as a
way to determine the location of internal files.

All operations are done using the 'install/core/bin/zoo_cmd'

Lets first setup zootools and add it to maya.
::

    cd zootoolspro
    call ./bin/zoo_cmd.bat setup --destination destination/folder --zip myZootools.zip --app maya --app_dir
    ~/Documents/maya/modules

In the case you want to install a new package you can use the '--install' flag.
Like the following.
::

    cd zootoolspro
    call ./bin/zoo_cmd.bat installPackage --path myPackagePath

You can also do --inPlace 1 if you want ot use the package directly without
::

    call ./bin/zoo_cmd.bat installPackage --path myPackagePath --inPlace


Git tags are also supported defined like so
::

    cd zootoolspro
    call install/core/bin/zoo_cmd.bat installPackage --path https:\\myGitpath.git --tag v1.0.0


.. note: 

    It's important to understand that a package.json file MUST exist
    under the package directory.
    Once installed the package will be located in.
    zootoolspro/install/packages/myPackage/{packageVersion}

Python
======

It's also Possible to run any CLI command via the python api

.. code-block:: python

    from zoo.core import api
    zoo = api.zooFromPath(os.environ["ZOOTOOLS_PRO_ROOT"])
    zoo.runCommand("installPackage" ("--path somePath/folder", "--inPlace"))