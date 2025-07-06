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


def generate_one_completion(prompt, client, model): # 生成一个问题的回答
    completion = client.chat.completions.create(
        model=model,
        stream=True,
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    full_response = ""
    for chunk in completion:
        if chunk.choices[0].delta and chunk.choices[0].delta.content:
            full_response += chunk.choices[0].delta.content
    pattern = r'```python\s*(.*?)\s*```'
    match = re.search(pattern, full_response, re.DOTALL)
    return match.group(1).strip() if match else None


def evaluate_single_task(task, generated_code): # 评估一个问题的回答
    task_id = task['task_id']
    test_code = task['test']
    entry_point = task['entry_point']
    result = {'task_id': task_id, 'completion': generated_code, 'passed': False, 'error': None}
    try:
        pd.options.mode.chained_assignment = None  # 关闭警告
        global_env = {'pd': pd, 'np': np, '__builtins__': __builtins__}
        # 加载测试用例
        exec(test_code, global_env)
        check_func = global_env['check']
        # 加载生成的代码
        exec(generated_code, global_env)
        candidate_func = global_env[entry_point]
        # 运行测试
        check_func(candidate_func)
        result['passed'] = True
    except SyntaxError as e:
        result['error'] = f'Syntax error: {str(e)}'
    except KeyError:
        result['error'] = f'Entry point {entry_point} not found'
    except AssertionError as e:
        result['error'] = f'Assertion failed: {str(e)}'
    except Exception as e:
        result['error'] = f'Runtime error: {str(e)}'
    return result


if __name__ == "__main__":
    base_url = sys.argv[1]
    api_key = sys.argv[2]
    model = sys.argv[3]
    idx = sys.argv[4]
    client = OpenAI(api_key=api_key, base_url=base_url)

    tasks = read_jsonl('datasets/PanNumEval/PanNumEval.jsonl')
    samples = []
    results = []

    # 多线程生成代码
    with ThreadPoolExecutor(max_workers=20) as executor:  # 可调整线程数
        # 创建生成任务列表
        gen_futures = [executor.submit(
            generate_one_completion,
            task["prompt"],
            client,
            model
        ) for task in tasks]

        # 使用tqdm包装进度显示
        samples = []
        for future in tqdm(gen_futures, desc="Generating Code", unit="task"):
            completion = future.result()
            samples.append({
                "task_id": f"PanNumEval/{len(samples)}",
                "completion": completion
            })

    # 多线程评估结果
    with ThreadPoolExecutor(max_workers=20) as executor:  # 可调整线程数
        # 准备评估参数
        eval_args = [(task, samples[i]["completion"])
                     for i, task in enumerate(tasks)]
        # 提交评估任务
        eval_futures = [executor.submit(
            evaluate_single_task,
            task,
            sample["completion"]
        ) for task, sample in zip(tasks, samples)]

        # 使用tqdm包装进度显示
        results = []
        for future in tqdm(eval_futures, desc="Evaluating Results", unit="task"):
            results.append(future.result())

    modelname = model.replace(" ", "").replace("-", "").replace(".", "")
    sorted_results = sorted(results, key=lambda x: int(x['task_id'].replace("PanNumEval/", ""))) # 按照编号进行排序
    for i in range(0, 50):
        # 使用参数化查询改写
        sql = f"INSERT INTO PanNumEval_{modelname}_samples_{idx} (task_id, completion) VALUES (%s, %s)"
        main.cursor.execute(sql, (str(sorted_results[i]['task_id']), str(sorted_results[i]['completion'])))

    main.cursor.execute(f"create TABLE PanNumEval_{modelname}_samples_{idx}_results (id INT AUTO_INCREMENT PRIMARY KEY, task_id VARCHAR(255), completion longtext, passed VARCHAR(255))")
    for i in range(0, 50):
        # 使用参数化查询改写
        sql = f"INSERT INTO PanNumEval_{modelname}_samples_{idx}_results (task_id, completion, passed) VALUES (%s, %s, %s)"
        main.cursor.execute(sql, (str(sorted_results[i]['task_id']), str(sorted_results[i]['completion']), str(sorted_results[i]['passed'])))