#!/usr/bin/env python3

import sys
import argparse

import auth

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("user", help="username")
    parser.add_argument("secret", help="secret hash to test")
    args = parser.parse_args()

    auth= auth.Auth() 
    if auth.check( args.user, args.secret ):
        print("Match")
        sys.exit(0)
    else:
        print("Mismatch")
        sys.exit(-1)
