import os
from dotenv import load_dotenv
load_dotenv()
import asyncio
import rag

try:
    print("Testing query_rag...")
    res = rag.query_rag("hello")
    print("Result:", res)
except Exception as e:
    print("Exception occurred:", repr(e))
