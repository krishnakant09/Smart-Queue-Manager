import os
import logging
import json
import urllib.request
import urllib.parse
import base64

class ReplitDB:
    """
    A wrapper for Replit's key-value database.
    This provides a simple interface for storing and retrieving data.
    """
    
    def __init__(self):
        self.db_url = os.environ.get("REPLIT_DB_URL")
        if not self.db_url:
            logging.warning("REPLIT_DB_URL environment variable not set. Using local storage.")
            self.local_storage = {}
            self.use_local = True
        else:
            self.use_local = False
    
    def set(self, key, value):
        """
        Store a value in the database.
        
        Args:
            key (str): The key to store the value under
            value (any): The value to store (will be JSON serialized)
        
        Returns:
            bool: True if the operation was successful
        """
        if self.use_local:
            self.local_storage[key] = value
            return True
        
        try:
            encoded_key = urllib.parse.quote(key)
            serialized_value = json.dumps(value)
            encoded_value = urllib.parse.quote(serialized_value)
            
            url = f"{self.db_url}/{encoded_key}"
            req = urllib.request.Request(url, data=encoded_value.encode("utf-8"), method="POST")
            urllib.request.urlopen(req)
            return True
        except Exception as e:
            logging.error(f"Error setting key {key}: {e}")
            return False
    
    def get(self, key, default=None):
        """
        Retrieve a value from the database.
        
        Args:
            key (str): The key to retrieve
            default (any): Default value if key doesn't exist
        
        Returns:
            any: The retrieved value or default
        """
        if self.use_local:
            return self.local_storage.get(key, default)
        
        try:
            encoded_key = urllib.parse.quote(key)
            url = f"{self.db_url}/{encoded_key}"
            
            try:
                with urllib.request.urlopen(url) as response:
                    if response.status == 200:
                        value = response.read().decode("utf-8")
                        return json.loads(value)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return default
                raise
            
            return default
        except Exception as e:
            logging.error(f"Error getting key {key}: {e}")
            return default
    
    def delete(self, key):
        """
        Delete a key from the database.
        
        Args:
            key (str): The key to delete
        
        Returns:
            bool: True if the operation was successful
        """
        if self.use_local:
            if key in self.local_storage:
                del self.local_storage[key]
                return True
            return False
        
        try:
            encoded_key = urllib.parse.quote(key)
            url = f"{self.db_url}/{encoded_key}"
            req = urllib.request.Request(url, method="DELETE")
            urllib.request.urlopen(req)
            return True
        except Exception as e:
            logging.error(f"Error deleting key {key}: {e}")
            return False
    
    def get_all(self, prefix=""):
        """
        Get all keys and values with a given prefix.
        
        Args:
            prefix (str): The prefix to filter keys by
        
        Returns:
            dict: A dictionary of keys and values
        """
        if self.use_local:
            return {k: v for k, v in self.local_storage.items() if k.startswith(prefix)}
        
        try:
            encoded_prefix = urllib.parse.quote(prefix)
            url = f"{self.db_url}?prefix={encoded_prefix}"
            
            with urllib.request.urlopen(url) as response:
                keys_text = response.read().decode("utf-8")
                if not keys_text:
                    return {}
                
                keys = keys_text.split("\n")
                result = {}
                
                for key in keys:
                    if key:  # Skip empty keys
                        value = self.get(key)
                        result[key] = value
                
                return result
        except Exception as e:
            logging.error(f"Error getting all keys with prefix {prefix}: {e}")
            return {}
