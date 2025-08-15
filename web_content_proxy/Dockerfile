ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python and system packages
RUN apk add --no-cache \
    python3 \
    py3-pip \
    jq

# Install Python packages
RUN pip3 install --no-cache-dir \
    flask==2.3.3 \
    requests==2.31.0 \
    beautifulsoup4==4.12.2 \
    lxml==4.9.3

# Copy data
COPY run.sh /
COPY proxy_server.py /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
