#!/bin/bash

export PYTHONPATH=$PYTHONPATH:./src
gunicorn src.wsgi:application
