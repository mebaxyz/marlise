
FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential liblilv-dev phantomjs
RUN apt-get install -y --no-install-recommends python3-pil python3-pystache python3-pip python3-setuptools
RUN apt-get install -y --no-install-recommends git pkg-config lv2-dev

ENV LV2_PATH="/lv2"

RUN git clone https://github.com/mebaxyz/mod-sdk.git /mod-sdk



WORKDIR /mod-sdk
RUN pip3 install -r requirements.txt
RUN python3 setup.py build

EXPOSE 9000
VOLUME ["/lv2"]

CMD ./development_server.py
