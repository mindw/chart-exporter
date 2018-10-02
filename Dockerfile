FROM python:3.6-alpine AS builder

COPY . /tmp
WORKDIR /tmp
RUN python3 setup.py bdist_wheel

FROM alpine:3.8

LABEL maintainer="Gabi Davar <grizzly.nyo@gmail.com>"

ENV PACKAGES "bash curl openssl less tini su-exec python3 yaml"
ENV DEV_PACKAGES "linux-headers build-base python3-dev yaml-dev"

RUN set -ex; \
    apk --no-cache add $PACKAGES; \
    pip3 --no-cache-dir --disable-pip-version-check install --no-compile -U pip setuptools; \
    find / \( -name \*.pyc -o -name \*.pyo -o -name __pycache__ \) -prune -exec rm -rf {} + ;

COPY --from=builder /tmp/dist/* /tmp/

RUN set -ex; \
    apk --no-cache add $DEV_PACKAGES; \
    pip3 --no-cache-dir --disable-pip-version-check install --no-compile cython; \
    pip3 --no-cache-dir --disable-pip-version-check install --no-compile -f /tmp chart_exporter; \
    find / \( -name \*.pyc -o -name \*.pyo -o -name __pycache__ \) -prune -exec rm -rf {} + ;\
    apk del $DEV_PACKAGES;\
    rm -rf /tmp/*

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks
# Python 3*, and that's not OK.
ENV LANG C.UTF-8

# set output to unbuffered to get the logs faster into docker
ENV PYTHONUNBUFFERED=0

RUN adduser -S chartexporter
USER chartexporter

ENTRYPOINT ["/sbin/tini", "--", "/usr/bin/chart_exporter"]
