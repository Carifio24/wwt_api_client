Releasing
=========

(Copied from ``pywwt``.)

To do a release, first edit the ``CHANGES.rst`` file to include the date of
the release after the version number, and make sure the changelog is up to
date.

Then edit the following files to update the version numbers:

* ``docs/conf.py``
* ``wwt_api_client/_version.py`` (make sure the string in the tuple is set to ``final``)

At this point, commit all changes and use the following for the commit
message::

    Preparing release v<version>

Now make sure there are no temporary files in the repository::

    git clean -fxd

and build the release files::

    python setup.py sdist bdist_wheel --universal

Go inside the ``dist`` directory, and you should see a tar file and a wheel.
At this point, if you wish, you can untar the tar file and try installing and
testing the installation. Once you are satisfied that the release is good you
can upload the release using twine::

    twine upload wwt_api_client-<version>.tar.gz wwt_api_client-<version>-py2.py3-none-any.whl

If you don't have twine installed, you can get it with ``pip install twine``.

At this point, you can tag the release with::

    git tag -m v<version> v<version>

If you have PGP keys set up, you can sign the tag by also including ``-s``.

Now change the versions in the files listed above to the next version — and
for the ``wwt_api_client/_version.py`` file, change ``final`` to ``dev``.
Commit the changes with::

    Back to development: v<next_version>
