from pecan import expose
from webob.exc import status_map

from ceph_updates.model.koji import Koji


class RootController(object):

    @expose(generic=True, template='index.j2')
    def index(self):
        koji = Koji()
        release = 'nautilus'
        tags = koji.tags(release)
        packages = koji.packages(release)
        builds = koji.builds(release)
        return {'tags': tags, 'packages': packages, 'builds': builds}

    @expose('error.j2')
    def error(self, status):
        try:
            status = int(status)
        except ValueError:  # pragma: no cover
            status = 500
        message = getattr(status_map.get(status), 'explanation', '')
        return dict(status=status, message=message)
