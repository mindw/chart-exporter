#!/usr/bin/env python

import sys
import click
from collections import Counter

from prometheus_async import aio

from prometheus_client import REGISTRY, Metric, generate_latest
from aiohttp import web
from . import tiller

_REF = '<html><body><a href="/metrics">Metrics</a></body></html>'


async def _cheap(request):
    return web.Response(text=_REF, content_type='text/html')


async def handle_healthz(request):
    return web.HTTPOk()


def start_app(host, port):
    app = web.Application()
    app.router.add_get('/', _cheap)
    app.router.add_get('/healthz', handle_healthz)
    app.router.add_get('/metrics', aio.web.server_stats)

    web.run_app(app, host = host, port=port)


@click.command()
@click.option('--metrics-address', default='0.0.0.0')
@click.option('--metrics-port', default=9484)
@click.option('--tiller-host', default='127.0.0.1')
@click.option('--tiller-port', default=44134)
@click.option('--tiller-timeout', default=300)
@click.option(
    '--tls', default=False, is_flag=True, help='enable TLS for request')
@click.option('--tls-ca-cert', help='path to tiller TLS CA certificate file')
@click.option('--tls-cert', help='path to client TLS certificate file')
@click.option(
    '--tls-hostname',
    help='the server name used to verify the hostname on the returned certificates from the server')  # noqa
@click.option('--tls-key', help='path to client TLS certificate key file')
@click.option(
    '--tls-verify',
    default=False,
    is_flag=True,
    help='enable TLS for request and verify remote'
)
def chart_exporter(
        metrics_address,
        metrics_port,
        tiller_host,
        tiller_port,
        tiller_timeout,
        tls,
        tls_ca_cert,
        tls_cert,
        tls_hostname,
        tls_key,
        tls_verify,
        one_shot
):

    collector = CustomCollector(tiller_host, tiller_port, tiller_timeout)
    REGISTRY.register(collector)
    if one_shot:
        stats = generate_latest()
        print(stats.decode())
    else:
        start_app(host=metrics_address, port=metrics_port)


class CustomCollector:
    def __init__(self, tiller_host, tiller_port, tiller_timeout):
        max_retries = 5
        for i in range(max_retries):
            try:
                self.tiller = tiller.Tiller(
                    host=tiller_host,
                    port=tiller_port,
                    timeout=tiller_timeout
                )
                break
            except Exception as e:
                print(e)
        else:
            print(
                f'Failed to connect to tiller on {tiller_host}:{tiller_port}')
            sys.exit(1)

    def collect(self):
        all_releases = self.tiller.list_releases()
        metric = Metric(
            'helm_chart_releases', 'Helm chart release information', 'gauge')
        chart_count = Counter(
            [
                (release.chart.metadata.name, release.chart.metadata.version)
                for release in all_releases
            ]
        )
        for chart in chart_count:
            metric.add_sample(
                'helm_chart_info',
                value=chart_count[chart],
                labels={
                    'name': chart[0],
                    'version': chart[1]
                }
            )
        yield metric
