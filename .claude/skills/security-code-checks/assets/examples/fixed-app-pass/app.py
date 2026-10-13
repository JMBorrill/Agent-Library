"""AI Operations Platform - booking API (synthetic, fixed version)."""
import json
import os

import jwt
import requests
import yaml
from argon2 import PasswordHasher
from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ["FLASK_SECRET_KEY"]
CORS(app, origins=["https://app.aiops.invalid"], supports_credentials=True)
DEBUG = False
_hasher = PasswordHasher()


def find_contacts(db, tenant_id, name):
    return db.execute("SELECT * FROM crm_contacts WHERE tenant_id = %s AND name = %s", (tenant_id, name))


def store_password(user, password):
    user.password_hash = _hasher.hash(password)


def load_import(blob, settings_text):
    data = json.loads(blob)
    settings = yaml.safe_load(settings_text)
    return data, settings


def sync_calendar(event):
    return requests.post("https://calendar.invalid/v1/events", json=event, timeout=5)


def current_user(token, public_key):
    return jwt.decode(token, public_key, algorithms=["RS256"], audience="aiops-api")
