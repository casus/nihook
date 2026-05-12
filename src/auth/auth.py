# auth module

import os
from base64 import b64encode, b64decode
import json
import hashlib
from pathlib import Path

"""
Class for local authentication 
"""
class Auth:

    '''
    Init from a JSON file
    '''
    def __init__(self, filepath = Path("auth.json") ):

        self.auth={}
        self.filepath=filepath

        try:
            with open(filepath,"r") as f:
                self.auth= json.load(f)
        except FileNotFoundError:
            print(f"New auth file {filepath}")
            with open(filepath, "w") as f:
                json.dump(self.auth, f, indent=4)


    def debug(self):
        print("Know users: ")
        for u in self.auth:
            print(f"    {u}")
    

    def list_users(self):
        if not self.auth:
            print("📭 No users found.")
            return
        print("\n📋 Existing users:")
        for u in self.auth:
            print(f"    {u}")
        print()
        

    def api_users_list(self):
        return self.auth

    def add( self, user_name : str, size : int = 64 ) -> str:

        if user_name in self.auth:
            print("⚠️ User already exists.")
            return ""

        if size < 32:
            print("⚠️ Size must be >= 32")
            return ""

        salt_bytes= os.urandom(size)
        secret_bytes= os.urandom(size)

        salt= b64encode(salt_bytes).decode('utf-8')
        secret= b64encode(secret_bytes).decode('utf-8')

        hash_bytes= hashlib.scrypt(secret_bytes, salt=salt_bytes, n= 2048, r= 8, p= 1, dklen=64 )
        hash= b64encode(hash_bytes).decode('utf-8')

        self.auth[user_name]={ "salt": salt, "hash": hash, "size": size}

        self.write()
        return secret

    def api_add(self, user_name: str, size: int = 64) -> str:
        if user_name in self.auth:
            raise ValueError(f"User '{user_name}' already exists.")

        if size < 32:
            raise ValueError("Size must be >= 32.")

        salt_bytes = os.urandom(size)
        secret_bytes = os.urandom(size)

        salt = b64encode(salt_bytes).decode('utf-8')
        secret = b64encode(secret_bytes).decode('utf-8')

        hash_bytes = hashlib.scrypt(
            secret_bytes,
            salt=salt_bytes,
            n=2048,
            r=8,
            p=1,
            dklen=64
        )
        hash_str = b64encode(hash_bytes).decode('utf-8')

        self.auth[user_name] = {
            "salt": salt,
            "hash": hash_str,
            "size": size
        }
        self.write()
        return secret


    '''
    Write out to auth file, needs to be called after one or more add() calls
    '''
    def write( self ):

        with open(self.filepath,"w+") as f:
            json.dump(self.auth,f,indent=4)


    def delete_user(self, user_name: str):
        if not user_name in self.auth:
            print(f"❌ User '{user_name}' not found.")
            return False
        del self.auth[user_name]
        print(f"🗑️ User '{user_name}' deleted.")
        self.write()
        return True

    def api_delete_user(self, user_name: str) -> str:
        if not user_name in self.auth:
            return f"'{user_name}' not found."
        del self.auth[user_name]
        print(f"🗑️ User '{user_name}' deleted.")
        self.write()
        return "User '{user_name}' deleted"

    '''
    Check b64 encoded secret if it matches for given user
    '''
    def check( self, user : str , secret : str ) -> bool:

        if (user == None or secret == None):
            print("Empty auth data")
            return False
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
