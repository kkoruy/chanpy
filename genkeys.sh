#!/bin/bash
mkdir ./keys
cd keys
pw=$(openssl passwd help)
uinp="$(echo $pw)
$(echo $pw)
"
openssl genrsa -passout stdin -out ca.key -aes256 2048 <<< "$pw"
cred="chanbot_db
chanbot@4mongodb.org
"
uinp="$(echo $pw)

.
.
.
.
$(echo $cred)
"


mkdir ./svr
mkdir ./clt
openssl req -new -x509 -key ./ca.key -out ./svr/serverca.crt -passin stdin <<< "$uinp"
openssl genrsa -out ./svr/server.key 2048
uinp="




$(echo $cred)


"
openssl req -new -key ./svr/server.key -out ./svr/server_reqout.txt <<< "$uinp"
cred="chanbot_cert
chanbot@4chan.org
"
uinp="$(echo $pw)





$(echo $cred)


"
openssl x509 -req -in ./svr/server_reqout.txt -days 3650 -sha512 -CAcreateserial -CA ./svr/serverca.crt -CAkey ./ca.key -out ./svr/server.crt -passin stdin <<< "$pw"

openssl genrsa -out ./clt/client.key 2048
openssl req -new -key ./clt/client.key -out ./clt/client_reqout.txt <<< "$uinp"
cred="chanbot
chanbot@pymongo.org
"
uinp="$(echo $pw)
.
.
.
.
.
$(echo $cred)
"
openssl x509 -req -in ./clt/client_reqout.txt -days 3650 -sha512 -CAcreateserial -CA ./svr/serverca.crt -CAkey ./ca.key -out ./clt/client.crt -passin stdin <<< "$uinp"
cd ..
cat ./keys/svr/server.crt ./keys/svr/server.key > ./docker/keys/tls/server.pem
cat ./keys/clt/client.crt ./keys/clt/client.key > ./db/keys/tls/client.pem
rm -rf ./keys

