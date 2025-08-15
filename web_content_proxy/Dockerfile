ARG BUILD_FROM
FROM $BUILD_FROM

# Install Python and required packages
RUN apk add --no-cache \
    python3 \
    py3-pip \
    py3-flask \
    py3-requests \
    py3-lxml \
    py3-beautifulsoup4

# Copy data
COPY run.sh /
COPY proxy_server.py /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
