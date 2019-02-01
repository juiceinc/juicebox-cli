.. Juicebox CLI documentation master file, created by
   sphinx-quickstart on Mon Aug 22 13:56:43 2016.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Juicebox CLI's documentation!
========================================

Installation
------------

To install the Juicebox command line interface (CLI), simply run this command in your terminal of choice::

    $ pip install juicebox-cli

If you don't have pip installed, this Python installation guide can guide you through the process.

Upgrading
---------

Occasionally, we release new versions of the juicebox-cli with an expanded feature sets or security updates. To upgrade juicebox-cli, run this command in your terminal::

    $ pip install -U juicebox-cli

Getting Started by Logging In
-----------------------------

After juicebox-cli has been installed, the juice command will be available. To begin using the CLI, we need to start by logging into Juicebox. Run the following command in your terminal replacing user@domain.com with the email of your Juicebox account and https://mydomain.juiceboxdata.com with the url of your production Juicebox account::

    $ juice login user@domain.com --endpoint https://mydomain.juiceboxdata.com

After typing this in, we will be prompted for our Juicebox account password. (Note: the account used must be a Juicebox client admin account. Contact Juicebox support if you need help obtaining a client admin account.)

If we are operating in an environment other than our normal production environment, we need to provide the corresponding environment's url via the ``--endpoint`` option::

    $ juice login user@domain.com --endpoint https://mydomain-dev.juiceboxdata.com

The above command will authenticate us with the 'dev' environment. You only need to repeat the login if you change your target endpoint, your password has changed, or your token has been invalidated.

Listing Available Clients
-------------------------

If we need a list of all the clients available for our account, we can use the client_list command to print out a display of them. For example::


    $ juice clients_list
    Client ID       Client Name
    --------------  -------------------------------------
    1               Juicebox

This command also accepts the ``--env`` flag, as shown here::

    $ juice clients_list --env dev
    Client ID       Client Name
    --------------  -------------------------------------
    1               Juicebox

Uploading Files
---------------

To upload files for use in ETL or User account creation, we use the upload command. The upload command accepts multiple arguments that can be file or directory names. If a directory is supplied, it will upload all the files in the directory. Let's look at some examples:

In its simplest from it only requires a filename, as shown here::

    $ juice upload records.csv

If we wanted to upload multiple files, we could do the following::

    $ juice upload records.csv clients.csv more_data.csv

If we wanted to upload all the files in the data directory we would issue the following command::

    $ juice upload data

The upload command also accepts the ``--env flag``, as shown here::

    $ juice upload --env dev records.csv

If we have access to multiple clients, we can use the ``--client`` option with a client identifier from the clients_list command to upload a file for a specific client. If you don't pass a client idea, it uses the lowest client identifier you have access too. Here is an example using the ``--client`` option::

    $ juice upload --env dev --client 1 records.csv

Also if we have access to multiple apps, we can use the ``--app`` option with an app slug upload a file for a specific app. If you don't pass an app, it uses just the client folder you have access too. Here is an example using the ``--app`` option::

    $ juice upload --env dev --client 1 --app data records.csv

Finally if we need to provide the location of the authentication file, we can use the ``--netrc`` option with the full path to the netrc file.  This can be useful for scheduled tasks on windows. The file is typically found in a users home directory and named .netrc on any POSIX operating system, and _netrc on any Windows system.  Here is an example from Windows::

    > juice upload --netrc c:\users\etl\_netrc records.csv
