import grpc
import yaml
import logging

from .hapi.services.tiller_pb2 import (
    ReleaseServiceStub,
    ListReleasesRequest,
    InstallReleaseRequest,
    UpdateReleaseRequest,
    UninstallReleaseRequest
)

from .hapi.chart.config_pb2 import Config

LOG = logging.getLogger(__name__)
TILLER_PORT = 44134
TILLER_VERSION = b'2.10.0'
TILLER_TIMEOUT = 300
RELEASE_LIMIT = 64


class Tiller:
    """
    The Tiller class supports communication and requests to the Tiller Helm
    service over gRPC
    """

    def __init__(self, host, port=44134, timeout=TILLER_TIMEOUT):

        # init k8s connectivity
        self._host = host
        self._port = port

        # init tiller channel
        self.channel = self.get_channel()

        # init timeout for all requests
        self.timeout = timeout

    @property
    def metadata(self):
        """
        Return tiller metadata for requests
        """
        return [(b'x-helm-api-client', TILLER_VERSION)]

    def get_channel(self):
        """
        Return a tiller channel
        """
        return grpc.insecure_channel(f'{self._host}:{self._port}')

    def tiller_status(self):
        """
        return if tiller exist or not
        """
        if self._host:
            return True

        return False

    def list_releases(self):
        """
        List Helm Releases
        """
        stub = ReleaseServiceStub(self.channel)
        req = ListReleasesRequest(limit=RELEASE_LIMIT)
        release_list = stub.ListReleases(
            req, self.timeout, metadata=self.metadata)
        releases = []
        for y in release_list:
            releases.extend(y.releases)
        return releases

    def list_charts(self):
        """
        List Helm Charts from Latest Releases

        Returns list of (name, version, chart, values)
        """
        charts = []
        for latest_release in self.list_releases():
            try:
                charts.append(
                    (
                        latest_release.name,
                        latest_release.version,
                        latest_release.chart,
                        latest_release.config.raw
                    )
                )
            except IndexError:
                continue
        return charts

    def update_release(
            self,
            chart,
            dry_run,
            name='',
            disable_hooks=False,
            values=None
    ):
        """
        Update a Helm Release
        """

        values = Config(raw=yaml.safe_dump(values or {}))

        # build release install request
        stub = ReleaseServiceStub(self.channel)
        release_request = UpdateReleaseRequest(
            chart=chart,
            dry_run=dry_run,
            disable_hooks=disable_hooks,
            values=values,
            name=name
        )

        stub.UpdateRelease(
            release_request,
            self.timeout,
            metadata=self.metadata
        )

    def install_release(
            self, chart, namespace, dry_run=False, name='', values=None):
        """
        Create a Helm Release
        """

        values = Config(raw=yaml.safe_dump(values or {}))

        # build release install request
        stub = ReleaseServiceStub(self.channel)
        release_request = InstallReleaseRequest(
            chart=chart,
            dry_run=dry_run,
            values=values,
            name=name,
            namespace=namespace)
        return stub.InstallRelease(
            release_request, self.timeout, metadata=self.metadata)

    def uninstall_release(self, release, disable_hooks=False, purge=True):
        """
        :params - release - helm chart release name
        :params - purge - deep delete of chart

        deletes a helm chart from tiller
        """

        # build release install request
        stub = ReleaseServiceStub(self.channel)
        release_request = UninstallReleaseRequest(
            name=release, disable_hooks=disable_hooks, purge=purge)
        return stub.UninstallRelease(
            release_request, self.timeout, metadata=self.metadata)

    def chart_cleanup(self, prefix, charts):
        """
        :params charts - list of yaml charts
        :params known_release - list of releases in tiller

        :result - will remove any chart that is not present in yaml
        """
        def release_prefix(prefix, chart):
            """
            how to attach prefix to chart
            """
            return f'{prefix}-{chart["chart"]["release_name"]}'

        valid_charts = [release_prefix(prefix, chart) for chart in charts]
        actual_charts = [x.name for x in self.list_releases()]
        chart_diff = list(set(actual_charts) - set(valid_charts))

        for chart in chart_diff:
            if chart.startswith(prefix):
                LOG.debug('Release: %s will be removed', chart)
                self.uninstall_release(chart)
