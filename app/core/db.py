import json
import os
import redis
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

CACHE_SERVER_URL = os.getenv('CACHE_SERVER_URL')
CACHE_SERVER_PORT = os.getenv('CACHE_SERVER_PORT')
redis_client  = redis.Redis(host=CACHE_SERVER_URL, port=CACHE_SERVER_PORT, decode_responses=True)

def set_cache(key: str, value: dict, ttl: int = 300):
    redis_client.set(key, json.dumps(value), ex=ttl)

def get_cache(key: str) -> dict:
    data_str = redis_client.get(key)
    if data_str:
        data = json.loads(data_str)
        return data
    return {}

def delete_cache(key: str):
    redis_client.delete(key)

def get_all_cache() -> dict:
    keys = redis_client.keys('*')
    all_data = {}
    for key in keys:
        all_data[key] = redis_client.hgetall(key)
    return all_data

