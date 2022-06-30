#!/bin/bash
IMAGE="guruevi/dcmsorter"
VERSION="0.5"
docker build . -t ${IMAGE}:${VERSION} --platform linux/amd64
docker tag ${IMAGE}:${VERSION} ${IMAGE}:latest
docker push ${IMAGE}:latest
