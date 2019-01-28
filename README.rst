web app for Ceph build updates

Current features:
-----------------

* Birds-eye view of what builds are in the `CBS (Koji)
  <https://cbs.centos.org/koji/>`_ system.

* Understand which builds can be promoted through -testing and -release.

Tags in CBS
-----------

You can manage builds through three tags:

1) ``-candidate``: When CBS completes a build, it immediately tags into
   ``-candidate``. This means the build is available for promoting to
   ``-testing`` and ``-release``.

2) ``-testing``: This build is in a `Yum repo
   <https://buildlogs.centos.org/>`_, ready for limited user testing.

3) ``-release``: This build is ready to be GPG-signed and go out to the CentOS
   mirror network for all users.

We want to manage this promotion process with a couple rules:
(note: not yet implemented in this application):

* All builds must go into ``-testing`` first, then into ``-release``.

* A build should go into the latest Ceph release first (eg. "Nautilus") before
  it goes into an older Ceph release (eg. "Mimic" or "Luminous").

* A build should be promoted through ``-testing`` and ``-release`` according
  to some quality rules (it passes some integration tests, and/or it's been in
  testing for X amount of days, etc).

We will also need to identify which container images correspond to a
combination of builds, so our container testing informs our test results.
