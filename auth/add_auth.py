#!/usr/bin/env python3

import sys
import os
from base64 import b64encode
import json
import argparse

import hashlib

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("user", help="username")
    args = parser.parse_args()

    auth={}

    filename= "auth"

    try:
        with open(filename,"r") as f:
            auth= json.load(f)
    except FileNotFoundError:
        print("File does not yet exist")

    if args.user in auth:
        print("User already existing, abort")
        sys.exit(-1)

    size= 32

    salt_bytes= os.urandom(size)
    secret_bytes= os.urandom(size)

    salt= b64encode(salt_bytes).decode('utf-8')
    secret= b64encode(secret_bytes).decode('utf-8')

    hash_bytes= hashlib.scrypt(secret_bytes, salt=salt_bytes, n= 2048, r= 8, p= 1, dklen=64 )
    hash= b64encode(hash_bytes).decode('utf-8')

    print(f"{secret}")

    auth[args.user]={ "salt": salt, "hash": hash}

    # print( json.dumps(auth,indent=4) )

    with open(filename,"w+") as f:
        json.dump(auth,f,indent=4)
