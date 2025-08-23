from debian:bookworm-slim


RUN apt-get update && apt-get install -y --no-install-recommends python3 git


RUN mkdir /data

RUN git clone https://github.com/bar0n/python-file-browser.git /app

WORKDIR /app


RUN sed -i "s|^.*current_dir *= *os.getcwd()|current_dir = '/data'|" main.py

ENTRYPOINT 
