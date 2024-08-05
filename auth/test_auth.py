#!/usr/bin/env python3

import os
from base64 import b64encode

size=64

salt= os.urandom(size)
token= b64encode(salt).decode('utf-8')

print(token)
