FROM my-mod-host
ENV REBUILD=true
ENV DEBIAN_FRONTEND=noninteractive

# Install dependencies
RUN apt-get update && apt-get install -q -y acl bc curl cvs git mercurial \
        rsync subversion wget bison bzip2 flex gawk gperf gzip help2man nano \ 
        perl patch tar texinfo unzip automake binutils build-essential cpio \ 
        libtool libncurses-dev pkg-config python-is-python3 libtool-bin premake bundler
ENV WORKDIR /mod/mod-plugin-builder/mod-workdir

# Build mod-host
RUN git clone https://github.com/moddevices/mod-plugin-builder.git --recursive /mod/mod-plugin-builder
RUN cd /mod/mod-plugin-builder && git submodule init && git submodule update
COPY ./copy_modguis.sh /mod/mod-plugin-builder 
RUN chmod +x /mod/mod-plugin-builder/copy_modguis.sh 


ARG PUID=1000
ARG PGID=1000
ENV PUID=${PUID}
ENV PGID=${PGID}
RUN mkdir /mod/plugins


RUN cd /mod/mod-plugin-builder && mkdir mod-workdir && chown abc mod-workdir \
    && gosu ${PUID} ./bootstrap.sh generic-aarch64 \
    
COPY ./build_mod_host.sh /mod/mod-plugin-builder/
RUN chmod +x /mod/mod-plugin-builder/build_mod_host.sh

ENTRYPOINT ["bash","-c"]



