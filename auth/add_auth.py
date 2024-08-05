#!/usr/bin/env python3

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
        os.exit(1)

    size=64

    salt= b64encode(os.urandom(size)).decode('utf-8')
    secret= b64encode(os.urandom(size)).decode('utf-8')

    hash= hashlib.scrypt(secret, salt=salt)

    print(f" {user} {salt} {secret} ")

