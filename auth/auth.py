# auth module

import os
from base64 import b64encode, b64decode
import json
import hashlib

"""
Class for local authentication 
"""
class Auth:

    '''
    Init from a JSON file
    '''
    def __init__(self, filename : str = "auth" ):

        self.auth={}
        self.filename=filename

        try:
            with open(filename,"r") as f:
                self.auth= json.load(f)
        except FileNotFoundError:
            print(f"New auth file {filename}")


        print("Know users: ")
        for u in self.auth:
            print(f"    {u}")


    def add( self, user : str, size : int = 64 ) -> str:

        if user in self.auth:
            print("User already existing")
            return ""

        if size < 32:
            print("Size must be >= 32")
            return ""

        salt_bytes= os.urandom(size)
        secret_bytes= os.urandom(size)

        salt= b64encode(salt_bytes).decode('utf-8')
        secret= b64encode(secret_bytes).decode('utf-8')

        hash_bytes= hashlib.scrypt(secret_bytes, salt=salt_bytes, n= 2048, r= 8, p= 1, dklen=64 )
        hash= b64encode(hash_bytes).decode('utf-8')

        self.auth[user]={ "salt": salt, "hash": hash, "size": size}

        return secret


    '''
    Write out to auth file, needs to be called after one or more add() calls
    '''
    def write( self ):

        with open(self.filename,"w+") as f:
            json.dump(self.auth,f,indent=4)

    '''
    Check b64 encoded secret if it matches for given user
    '''
    def check( self, user : str , secret : str ) -> bool:

        if user not in self.auth:
            print("User unknown")
            return False

        record= self.auth[user]

        if "salt" not in record or "hash" not in record or "size" not in record:
            print("Entry incomplete, abort")
            return False

        salt= record['salt']
        secret= secret

        if len(salt) != len(secret):
            print("Length mismatch")
            return False

        salt_bytes= b64decode(salt)
        secret_bytes= b64decode(secret)

        salt_len= len(salt_bytes)
        # print("len=", salt_len)

        hash_bytes= hashlib.scrypt(secret_bytes, salt=salt_bytes, n= 2048, r= 8, p= 1, dklen=64 )
        hash= b64encode(hash_bytes).decode('utf-8')

        # print(f"{hash}")
        # print(f"{record['hash']}")

        return hash == record['hash']
