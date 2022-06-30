FROM alpine:latest
RUN apk update
RUN apk add --no-cache python3 py-pip
COPY . /app
RUN pip install -r /app/requirements.txt
RUN pip install -r /app/requirements_calpendo.txt
VOLUME ["/app/config"]
CMD /usr/bin/python3 /app/sorter.py