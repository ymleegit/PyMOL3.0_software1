#!/bin/bash

find . -name \*.pyc -exec rm {} \;
find . -name __pycache__ -exec rm -r {} \;

