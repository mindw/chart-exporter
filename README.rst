Prometheus metrics exporter for Helm Tiller
===========================================

.. image:: https://img.shields.io/pypi/v/chart-exporter.svg
    :alt: PyPI

.. image:: https://img.shields.io/pypi/pyversions/chart-exporter.svg
    :alt: PyPI - Python Version

.. image:: https://quay.io/repository/grizzly_nyo/chart-exporter/status
    :target: https://quay.io/repository/grizzly_nyo/chart-exporter
    :alt: Docker Repository on Quay

.. image:: https://img.shields.io/badge/license-MIT-orange.svg?style=flat-square
    :target: http://opensource.org/licenses/MIT


Metrics look like this..

::

   # HELP helm_chart_info Helm chart information
   # TYPE helm_chart_info gauge
   helm_chart_info{name="nginx-ingress",version="0.28.2"} 1.0
   helm_chart_info{name="prometheus",version="7.0.3"} 1.0
   helm_chart_info{name="grafana",version="1.14.6"} 1.0

This dynamically updates as you add and remove charts.

You can then make pretty Grafana dashboards showing installed Helm
package versions.

See
https://www.robustperception.io/exposing-the-software-version-to-prometheus
for more info.
