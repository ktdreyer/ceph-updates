from collections import defaultdict
from datetime import datetime, timedelta
import os
from pecan import conf
import koji

import logging

logger = logging.getLogger(__name__)


# Default time a package must wait in -testing
WAIT_PERIOD = timedelta(days=14)


def get_session(profile):
    """
    Return an anonymous koji session for KOJI_PROFILE.

    :profile str: eg "cbs"
    :returns: anonymous koji.ClientSession
    """
    mykoji = koji.get_profile_module(profile)
    # Workaround https://pagure.io/koji/issue/1022 . Koji 1.17 will not need
    # this.
    if '~' in str(mykoji.config.cert):
        mykoji.config.cert = os.path.expanduser(mykoji.config.cert)
    if '~' in str(mykoji.config.ca):
        mykoji.config.ca = os.path.expanduser(mykoji.config.ca)
    opts = vars(mykoji.config)
    # Force an anonymous session (noauth):
    opts['noauth'] = True
    session = mykoji.ClientSession(mykoji.config.server, opts)
    return session


class Koji(object):
    def __init__(self):
        self.profile = conf.koji['profile']
        self.session = get_session(self.profile)

    def tags(self, release):
        results = {
            'candidate': 'storage7-ceph-nautilus-candidate',
            'testing': 'storage7-ceph-nautilus-testing',
            'release': 'storage7-ceph-nautilus-release',
        }
        return results

    def packages(self, release):
        """ All package names for this release's tags. """
        tags = self.tags(release)
        self.session.multicall = True
        for tag in tags.values():
            self.session.listPackages(tag)
        results = self.session.multiCall(strict=True)
        self.session.multicall = False
        all_packages = set()
        for tag_packages in results:
            tag_packages = tag_packages[0]  # expand multicall result
            names = set([package['package_name'] for package in tag_packages])
            all_packages.update(names)
        return sorted(all_packages)

    def builds(self, release):
        """
        {'candidate': {'ceph-ansible': buildinfo, 'ceph': buildinfo},
         'testing':   {'ceph-ansible': buildinfo, 'ceph': buildinfo},
         'release':   {'ceph-ansible': buildinfo, 'ceph': buildinfo}}
        """
        tags = self.tags(release)
        tag_keys = tags.keys()
        self.session.multicall = True
        for tag_key in tag_keys:
            tag_name = tags[tag_key]
            self.session.listTagged(tag_name, latest=True)
        results = self.session.multiCall(strict=True)
        self.session.multicall = False
        results = [result[0] for result in results]  # expand multicall result
        keys_and_builds = list(zip(tag_keys, results))

        # Find the time at which each build was tagged.
        self.session.multicall = True
        opts = {'limit': 1, 'order': '-create_event'}
        for tag_key, tag_builds in keys_and_builds:
            tag = tags[tag_key]
            for build in tag_builds:
                self.session.tagHistory(tag=tag, build=build['nvr'],
                                        active=True, queryOpts=opts)
        histories = self.session.multiCall(strict=True)
        self.session.multicall = False
        tag_histories = defaultdict(dict)
        for history in histories:
            # Koji multicall results end up in a list.
            # Each tagHistory call also returns a list with a single item.
            # so we have single-item lists of single-item lists. Flatten this.
            history = history[0][0]
            tag_name = history['tag_name']
            tag_key = next((key for key, name in tags.items()
                            if name == tag_name))
            package_name = history['name']
            create_ts = datetime.utcfromtimestamp(history['create_ts'])
            tag_histories[tag_key][package_name] = create_ts

        builds = {}
        now = datetime.utcnow()
        for tag_key, tag_builds in keys_and_builds:
            builds_by_name = {}
            for buildinfo in tag_builds:
                name = buildinfo['name']
                # "version-release" convenience string
                vr = '%s-%s' % (buildinfo['version'], buildinfo['release'])
                buildinfo['vr'] = vr
                # Add the duration this build was tagged:
                tagged_time = tag_histories[tag_key][name]
                tagged_duration = now - tagged_time
                buildinfo['tagged_duration'] = tagged_duration
                builds_by_name[name] = buildinfo
            builds[tag_key] = builds_by_name

        # Can we promote this build?
        # promote_state options:
        # * "ready", ready to promote now.
        # * "waiting", still in testing period.
        # * "paused", user manually indicated there is a problem.
        # * "complete", there is no newer version to promote.
        # * "released", cannot promote any further.
        for tag_key, tag_builds in builds.items():
            for name, buildinfo in tag_builds.items():
                if tag_key == 'candidate':
                    testing_build = builds['testing'].get(name)
                    if testing_build and testing_build['vr'] == buildinfo['vr']:
                        buildinfo['promote_state'] = 'complete'
                    else:
                        buildinfo['promote_state'] = 'ready'
                elif tag_key == 'testing':
                    release_build = builds['release'].get(name)
                    if release_build and release_build['vr'] == buildinfo['vr']:
                        buildinfo['promote_state'] = 'complete'
                    else:
                        # The duration until this build can be promoted.
                        remaining = WAIT_PERIOD - buildinfo['tagged_duration']
                        logger.info('%s remaining %s' % (name, remaining))
                        if remaining.total_seconds() < 0:
                            buildinfo['promote_state'] = 'ready'
                        else:
                            buildinfo['promote_state'] = 'waiting'
                            buildinfo['wait_remaining'] = remaining
                elif tag_key == 'released':
                    buildinfo['promote_state'] = 'released'
        return builds
