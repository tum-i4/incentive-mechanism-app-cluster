#!/bin/bash
rm agatha.db
poetry run python3 executables/add_sample_data.py
poetry run python3 executables/run-agatha.py --dev
