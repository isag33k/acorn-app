#!/bin/bash
export DATABASE_URL="postgresql://acorn_user:Welcome1@localhost/acorn" 
cd /home/sjones/acorn-app
source /home/sjones/acorn-app/venv/bin/activate
exec gunicorn --bind 127.0.0.1:5000 main:app
