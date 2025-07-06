from click import prompt
from openai import OpenAI
import os
import warnings
import tempfile
import subprocess
import re
import json

with open("APIDocs.json",'r',encoding='utf-8') as load_f:
    APIDocs = json.load(load_f)

with open("RustEvo^2.json",'r',encoding='utf-8') as load_f:
    RustEvo = json.load(load_f)

results = []
for i in range(0, len(APIDocs)):
    # del APIDocs[i]["from_version"]
    # del APIDocs[i]["to_version"]
    APIDocs[i].update(RustEvo[i])
    results.append(APIDocs[i])

with open("Evaluate/example.json", 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)