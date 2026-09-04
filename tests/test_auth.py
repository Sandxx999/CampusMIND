import sys
import os
import pytest

# Ensure backend folder is in sys.path for importing backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from auth.jwt_handler import create_access_token, decode_access_token

def test_jwt_generation_and_decoding():
    payload = {"sub": "student1", "role": "student"}
    token = create_access_token(payload)
    
    assert isinstance(token, str)
    assert len(token) > 20
    
    decoded = decode_access_token(token)
    assert decoded is not None
    assert decoded["sub"] == "student1"
    assert decoded["role"] == "student"

def test_invalid_token_decoding():
    invalid_token = "invalid.jwt.token.string"
    decoded = decode_access_token(invalid_token)
    assert decoded is None
