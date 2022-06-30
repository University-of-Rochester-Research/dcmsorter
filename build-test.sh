#!/bin/bash
docker rm dcmsorter_test
rm -rf test-data/out/*
cp config/* myconfig/
docker run --mount type=bind,source="$(pwd)"/test-data/in,target=/in \
           --mount type=bind,source="$(pwd)"/test-data/out,target=/out \
           --mount type=bind,source="$(pwd)"/myconfig,target=/app/config \
           --name dcmsorter_test \
           -d guruevi/dcmsorter
sleep 5
docker logs dcmsorter_test