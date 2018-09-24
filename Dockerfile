FROM python:3.6-alpine AS builder

COPY . /tmp
WORKDIR /tmp
RUN python3 setup.py bdist_wheel

FROM alpine:3.8

LABEL maintainer="SaaS Platform Team <iot-saas-platform@arm.com>"

ENV PACKAGES "bash curl openssl ca-certificates less tini su-exec python3"

RUN set -ex; \
    apk --no-cache add $PACKAGES; \
    pip3 --no-cache-dir --disable-pip-version-check install --no-compile -U pip setuptools; \
    find / \( -name \*.pyc -o -name \*.pyo -o -name __pycache__ \) -prune -exec rm -rf {} + ;

COPY --from=builder /tmp/dist/* /tmp/

RUN set -ex; \
    pip3 --no-cache-dir --disable-pip-version-check install --no-compile -f /tmp coreos_aws_helper; \
    find / \( -name \*.pyc -o -name \*.pyo -o -name __pycache__ \) -prune -exec rm -rf {} + ;\
    rm -rf /tmp/*

# http://bugs.python.org/issue19846
# > At the moment, setting "LANG=C" on a Linux system *fundamentally breaks
# Python 3*, and that's not OK.
ENV LANG C.UTF-8

# set output to unbuffered to get the logs faster into docker
ENV PYTHONUNBUFFERED=0

RUN adduser -S coreoshelper
USER coreoshelper

ENTRYPOINT ["/sbin/tini", "--", "/usr/bin/coreos-aws-helper"]

FROM python:alpine
COPY src/ /app
WORKDIR /app
RUN apk add --no-cache gcc linux-headers make musl-dev python-dev g++
RUN pip install -r requirements.txt
EXPOSE 9484
CMD python ./kubedex.py
