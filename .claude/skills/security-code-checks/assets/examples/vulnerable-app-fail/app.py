"""AI Operations Platform - booking API (synthetic, deliberately vulnerable)."""
import hashlib
import pickle

import jwt
import requests
import yaml
from flask import Flask, request
from flask_cors import CORS

app = Flask(__name__)
app.config["SECRET_KEY"] = "sk-FAKE-0000-do-not-use"
AWS_ACCESS_KEY_ID = "AKIAFAKEFAKEFAKEFAKE"
CORS(app, origins="*", supports_credentials=True)
DEBUG = True


def find_contacts(db, tenant_id, name):
    return db.execute(f"SELECT * FROM crm_contacts WHERE tenant_id = '{tenant_id}' AND name = '{name}'")


def store_password(user, password):
    user.password_hash = hashlib.md5(password.encode()).hexdigest()


def load_import(blob, settings_text):
    data = pickle.loads(blob)
    settings = yaml.load(settings_text)
    return data, settings


def sync_calendar(event):
    return requests.post("https://calendar.invalid/v1/events", json=event, verify=False, timeout=5)


def current_user(token):
    return jwt.decode(token, options={"verify_signature": False})
