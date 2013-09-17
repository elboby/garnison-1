garnison
========

Web interface for the package building and deployment tool.

Installation
============

To launch the webserver:

    $ cd garnison
    $ mkvirtualenv garnison
    $ pip install --upgrade -r requirements.pip
    $ GACHETTE_SETTINGS=./config.rc ./runserver.py
    
It can also run as a uwsgi app.

To launch the celery consumer:

    $ cd garnison
    $ GACHETTE_SETTINGS="./config.rc" celery -A gachette_web.tasks worker -l debug --purge

You will need to have an instance of Redis running as well and configured in the `config.rc` file.

The build machine needs to have installed `trebuchet`:

    $ git clone git@github.com:ops-hero/trebuchet.git
    $ cd trebuchet
    $ sudo python setup.py install
    $ trebuchet --version


Todo
====

* authentication (github oauth)
* webui+websocket
* logs / error handling
