#!/usr/bin/env bash
uvicorn main:app --host 127.0.0.1 --port 8000 &
streamlit run app.py --server.port 7860 --server.address 0.0.0.0
