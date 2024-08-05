#!/usr/bin/env python3

import sys
import os
from base64 import b64encode, b64decode
import json
import argparse

import hashlib

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("user", help="username")
    parser.add_argument("secret", help="secret hash to test")
    args = parser.parse_args()

    auth={}

    filename= "auth"

    try:
        with open(filename,"r") as f:
            auth= json.load(f)
    except FileNotFoundError:
        print("File does not exist, abort")
        sys.exit(-11)

    if args.user not in auth:
        print("User unknown, abort")
        sys.exit(-12)

    record= auth[args.user]

    if "salt" not in record or "hash" not in record:
        print("Entry incomplete, abort")
        sys.exit(-13)

    size= 32

    salt= record['salt']
    secret= args.secret

    salt_bytes= b64decode(salt)
    secret_bytes= b64decode(secret)

    hash_bytes= hashlib.scrypt(secret_bytes, salt=salt_bytes, n= 2048, r= 8, p= 1, dklen=64 )
    hash= b64encode(hash_bytes).decode('utf-8')

    print(f"{hash}")
    print(f"{record['hash']}")

    if hash == record['hash']:
        print("Match")
        sys.exit(0)
    else:
        print("Mismatch")
        sys.exit(-1)