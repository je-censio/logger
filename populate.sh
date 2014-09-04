#!/bin/bash

hostname=localhost:8080

# catch any failures -- we're running with curl -f
set -e

# make some users
for x in $(seq 1 5); do
    curl $hostname/register-user/name/user-$x/email/user-$x@gmail.com/password/pw-$x -s -f >/dev/null
done

# register some devices
for x in $(seq 1 5); do
    curl $hostname/register-device/user/user-$x/device/dev-$x --user user-$x:pw-$x -s -f >/dev/null
done

curl $hostname/store/user/user-1/device/dev-1/method/get/url/http:%2f%2fgoogle.com --user user-1:pw-1  -s -f >/dev/null
curl $hostname/store/user/user-1/device/dev-1/method/get/url/http:%2f%2fgoogle.com%2findex.html --user user-1:pw-1 -s -f >/dev/null
curl $hostname/store/user/user-1/device/dev-1/method/get/url/http:%2f%2fgoogle.com%2fstuff.html --user user-1:pw-1 -s >/dev/null
curl $hostname/store/user/user-3/device/dev-3/method/get/url/http:%2f%2fwhat.com --user user-3:pw-3 -s -f >/dev/null
curl $hostname/store/user/user-2/device/dev-2/method/get/url/http:%2f%2fgoogle.com --user user-2:pw-2 -s -f >/dev/null
curl $hostname/store/user/user-4/device/dev-4/method/put/url/http:%2f%2fwhat.com --user user-4:pw-4 -s -f >/dev/null
curl $hostname/store/user/user-4/device/dev-4/method/put/url/http:%2f%2fgoogle.com --user user-4:pw-4 -s -f >/dev/null
