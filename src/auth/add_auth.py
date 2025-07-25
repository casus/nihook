#!/usr/bin/env python3

import argparse

import auth

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("user", help="username")
    parser.add_argument("--size", type=int, default=32, help="Length of secret in bytes")
    args = parser.parse_args()

    auth= auth.Auth() 

    secret= auth.add(args.user, args.size)

    if "" != secret:
        print( secret )
    else:
        print("failed")

    auth.write()
