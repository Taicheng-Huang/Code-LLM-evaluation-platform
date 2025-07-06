import json
import time

from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import pymysql
import importlib
import sys
import os
from pymysql.cursors import DictCursor

# model = "deepseek-v3-250324" # 选择你要用的模型
model = "qwen-max-latest"
# model = "gpt41nano"
# model = "qwen3-235b-a22b"
# dataset = "human-eval"
# dataset = "PanNumEval"
# dataset = "NumpyEval"
# dataset = "PandasEval"
# dataset = "RustEvo"
# dataset = "CodeApex"
dataset = "cruxeval"

def create_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='abc88668866',
        database='shixun',
        autocommit=True
    )

modelname = model.replace(" ", "").replace("-", "").replace(".", "")
idx = 0
db = create_db_connection()
cursor = db.cursor()
# cursor.execute(f"SELECT COUNT(*) FROM {dataset}_{modelname}_results_{idx} where passed = 'True'")
cursor.execute(f"SELECT COUNT(*) FROM {dataset}_{modelname}_results_{idx} where LLM_input_passed = 'True'")
count = cursor.fetchone()[0]
print(count)
