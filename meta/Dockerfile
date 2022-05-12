FROM debian:buster
COPY deps/yate_5.5-1_amd64.deb /tmp/
RUN apt update && apt install -y -f /tmp/yate_5.5-1_amd64.deb python3-pip
RUN pip3 install python-yate requests
COPY config /etc/yate
COPY sounds /opt/sounds
COPY yate /usr/share/yate/scripts/
ENTRYPOINT [ "/usr/bin/yate", "upstream_broke_it" ]
