#!/bin/bash

# do some simple setup with riak. Create some buckets to store counters
# and don't allow siblings on Write-once buckets.

sudo riak-admin bucket-type create counters '{"props":{"datatype":"counter"}}'
sudo riak-admin bucket-type activate counters

curl localhost:8098/buckets/Users/props -H 'Content-Type: application/json' -d '{"props": {"allow_mult": false}}' -XPUT
curl localhost:8098/buckets/Devices/props -H 'Content-Type: application/json' -d '{"props": {"allow_mult": false}}' -XPUT
curl localhost:8098/buckets/Logs/props -H 'Content-Type: application/json' -d '{"props": {"allow_mult": false}}' -XPUT

