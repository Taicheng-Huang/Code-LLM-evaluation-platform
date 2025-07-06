import pandas as pd
import numpy as np
import re
import sys
from openai import OpenAI
import json
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from src import main

def read_jsonl(file_path): # 读取数据集数据
    with open(file_path, 'r', encoding='utf-8') as file:
        data = [json.loads(line) for line in file]
    return data

def make_direct_output_prompt(code, input):
    return f"""You are given a Python function and an assertion containing an input to the function. Complete the assertion with a literal (no unsimplified expressions, no function calls) containing the output when executing the provided code on the given input, even if the function is incorrect or incomplete. Do NOT output any extra information. Provide the full assertion with the correct output in [ANSWER] and [/ANSWER] tags, following the examples.

[PYTHON]
def f(n):
    return n
assert f(17) == ??
[/PYTHON]
[ANSWER]
17
[/ANSWER]

[PYTHON]
def f(s):
    return s + "a"
assert f("x9j") == ??
[/PYTHON]
[ANSWER]
"x9ja"
[/ANSWER]

[PYTHON]
{code}
assert f({input}) == ??
[/PYTHON]
[ANSWER]
"""

def make_direct_input_prompt(code, output):
    return f"""You will be given a function f and an output in the form f(??) == output. Find any input such that executing f on the input leads to the given output. There may be multiple answers, but you should only output one. In [ANSWER] and [/ANSWER] tags, complete the assertion with one such input that will produce the output when executing the function.

[PYTHON]
def f(my_list):
    count = 0
    for i in my_list:
        if len(i) % 2 == 0:
            count += 1
    return count
assert f(??) == 3
[/PYTHON]
[ANSWER]
["mq", "px", "zy"]
[/ANSWER]

[PYTHON]
def f(s1, s2):
    return s1 + s2
assert f(??) == "banana"
[/PYTHON]
[ANSWER]
"ba", "nana"
[/ANSWER]

[PYTHON]
{code}
assert f(??) == {output}
[/PYTHON]
[ANSWER]
"""

def generate_one_completion(code, input, output, client, model): # 生成一个问题的回答
    completion1 = client.chat.completions.create(
        model=model,
        stream=True,
        messages=[
            {"role": "user", "content": make_direct_input_prompt(code, output)}
        ]
    )
    full_response1 = ""
    for chunk in completion1:
        if chunk.choices[0].delta and chunk.choices[0].delta.content:
            full_response1 += chunk.choices[0].delta.content
    full_response1 = full_response1.replace("[/ANSWER]", "").replace("\"","\'").replace("\n","")

    completion2 = client.chat.completions.create(
        model=model,
        stream=True,
        messages=[
            {"role": "user", "content": make_direct_output_prompt(code, input)}
        ]
    )
    full_response2 = ""
    for chunk in completion2:
        if chunk.choices[0].delta and chunk.choices[0].delta.content:
            full_response2 += chunk.choices[0].delta.content
    full_response2 = full_response2.replace("[/ANSWER]", "").replace("\"","\'").replace("\n","")

    return full_response1, full_response2

if __name__ == "__main__":
    base_url = sys.argv[1]
    api_key = sys.argv[2]
    model = sys.argv[3]
    idx = sys.argv[4]
    client = OpenAI(api_key=api_key, base_url=base_url)

    tasks = read_jsonl('datasets/cruxeval/cruxeval.jsonl')
    samples = []

    # 多线程生成代码
    with ThreadPoolExecutor(max_workers=20) as executor:  # 可调整线程数
        # 创建生成任务列表
        gen_futures = [executor.submit(
            generate_one_completion,
            task["code"],
            task["input"],
            task["output"],
            client,
            model
        ) for task in tasks]

        # 使用tqdm包装进度显示
        samples = []
        for future in tqdm(gen_futures, desc="Getting results", unit="task"):
            completion1, completion2 = future.result()

            LLM_input_passed = "True"
            if completion1 == str(tasks[len(samples)]["input"]):
                LLM_input_passed = "True"
            else:
                LLM_input_passed = "False"

            LLM_output_passed = "True"
            if completion2 == str(tasks[len(samples)]["output"]):
                LLM_output_passed = "True"
            else:
                LLM_output_passed = "False"

            samples.append({
                "task_id": f"cruxeval/{len(samples)}",
                "input": tasks[len(samples)]["input"],
                "output": tasks[len(samples)]["output"],
                "LLM_input": completion1,
                "LLM_output": completion2,
                "LLM_input_passed": LLM_input_passed,
                "LLM_output_passed": LLM_output_passed
            })

    modelname = model.replace(" ", "").replace("-", "").replace(".", "")
    sorted_samples = sorted(samples, key=lambda x: int(x['task_id'].replace("cruxeval/", ""))) # 按照编号进行排序
    for i in range(0, 800):
        # 使用参数化查询改写
        sql = f"INSERT INTO cruxeval_{modelname}_results_{idx} (task_id, input, output, LLM_input, LLM_output, LLM_input_passed, LLM_output_passed) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        main.cursor.execute(sql, (str(sorted_samples[i]['task_id']),
                                  str(sorted_samples[i]['input']),
                                      str(sorted_samples[i]['output']),
                                          str(sorted_samples[i]['LLM_input']),
                                              str(sorted_samples[i]['LLM_output']),
                                                  str(sorted_samples[i]['LLM_input_passed']),
                                                      str(sorted_samples[i]['LLM_output_passed'])
                                                      ))