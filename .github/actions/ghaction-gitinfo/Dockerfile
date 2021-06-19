FROM debian:buster

ENV DEBIAN_FRONTEND noninteractive
RUN set -e -x; \
    apt-get update; \
    apt-get install -y --no-install-recommends git python3

COPY entrypoint /
CMD /entrypoint
