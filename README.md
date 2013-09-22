garnison
========

Web interface for the package building and deployment tool.

Installation
============

To launch the webserver:

    $ cd garnison
    $ mkvirtualenv garnison
    $ pip install --upgrade -r requirements.pip
    $ GACHETTE_SETTINGS=./config_vagrant.rc ./manage.py runserver
    
It can also run as a uwsgi app.

To launch the celery consumer:

    $ cd garnison
    $ GACHETTE_SETTINGS=./config_vagrant.rc celery -A gachette_web.tasks worker -l debug --purge

You will need to have an instance of Redis running as well and configured in the `config.rc` file.
By using `config_vagrant`, you will actually use the one in Bidasse/Vagrant VM.

The build machine needs to have installed `trebuchet`:

    $ git clone git@github.com:ops-hero/trebuchet.git
    $ cd trebuchet
    $ sudo python setup.py install
    $ trebuchet --version


Todo
====

* authentication (github oauth)
* websocket
* logs / error handling
* locking (not build the projects in // for 1 stack)
* integration with mise-a-feu
* status page for deployment, hosts
* replace meta api for stack
