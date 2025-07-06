import json
import sys
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from src import main
import concurrent.futures

# 读取JSON文件
def read_json():
    with open('datasets/CodeApex/testcases_zh.json', 'r', encoding='utf-8') as f:
        data = json.load(f)  # 解析JSON数据为Python列表
    return data

def make_prompt(question, a, b, c, d):
    return f"""该题所设选项中只有一个正确答案，请你输出正确答案的字母标号(如A、B)，除此以外不能输出任何其它内容

问题: {question}
A: {a}
B: {b}
C: {c}
D: {d}
"""

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
    return full_response

# 处理单个任务
def process_one_task(item, client, model):
    # 提取字段
    question = item["question"]
    option_a = item["A"]
    option_b = item["B"]
    option_c = item["C"]
    option_d = item["D"]
    category = item["category"]
    q_id = item["id"]

    prompt = make_prompt(question, option_a, option_b, option_c, option_d)

    answer = generate_one_completion(prompt, client, model)

    passed = "False"

    if (answer == "A" or answer == "a") and category == 0:
        passed = "True"
    elif (answer == "B" or answer == "b") and category == 1:
        passed = "True"
    elif (answer == "C" or answer == "c") and category == 2:
        passed = "True"
    elif (answer == "D" or answer == "d") and category == 3:
        passed = "True"

    return {
        "task_id": f"CodeApex/{q_id}",  # 使用原始ID保证唯一性
        "LLM_answer": answer,
        "passed": passed
    }

if __name__ == "__main__":
    base_url = sys.argv[1]
    api_key = sys.argv[2]
    model = sys.argv[3]
    idx = sys.argv[4]
    client = OpenAI(api_key=api_key, base_url=base_url)

    tasks = read_json()

    samples = []

    with ThreadPoolExecutor(max_workers=20) as executor:
        # 提交所有任务到线程池
        future_to_item = {
            executor.submit(process_one_task, item, client, model): item
            for item in tasks
        }

        # 使用tqdm创建进度条
        futures = list(future_to_item.keys())
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            try:
                result = future.result()
                samples.append(result)
            except Exception as e:
                print(f"处理任务时出错: {e}")

    modelname = model.replace(" ", "").replace("-", "").replace(".", "")
    sorted_samples = sorted(samples, key=lambda x: int(x['task_id'].replace("CodeApex/", "")))  # 按照编号进行排序
    for i in range(0, 250):
        # 使用参数化查询改写
        sql = f"INSERT INTO CodeApex_{modelname}_results_{idx} (task_id, LLM_answer, passed) VALUES (%s, %s, %s)"
        main.cursor.execute(sql, (str(sorted_samples[i]['task_id']),str(sorted_samples[i]['LLM_answer']),str(sorted_samples[i]['passed'])))
