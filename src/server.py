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

app = Flask(__name__)
CORS(app)  # 启用 CORS

def create_db_connection():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='abc88668866',
        database='shixun',
        autocommit=True
    )

def find_available_index(cursor, table_prefix):
    for i in range(0, 100):
        cursor.execute(f"SHOW TABLES LIKE '{table_prefix}_{str(i)}'")
        if not cursor.fetchone():
            return i
    return None


def execute_dataset_logic(base_url, api_key, model, dataset):
    modelname = model.replace(" ", "").replace("-", "").replace(".", "")
    db = create_db_connection()
    cursor = db.cursor()

    print("base_url: " + base_url)
    print("api_key: " + api_key)
    print("model: " + model)
    print("dataset: " + dataset)

    try:
        idx = -1
        if dataset == "human_eval" or dataset == "HumanEval":
            idx = find_available_index(cursor, f"human_eval_{modelname}_samples")
            cursor.execute(f"CREATE TABLE human_eval_{modelname}_samples_{idx} (id INT AUTO_INCREMENT PRIMARY KEY, task_id VARCHAR(255), completion LONGTEXT)")

            os.system(f"python datasets//human_eval//get_samples.py {base_url} {api_key} {model} {idx}")
            os.system(f"python datasets//human_eval//get_results.py {base_url} {api_key} {model} {idx}")

            cursor.execute(f"SELECT COUNT(*) FROM human_eval_{modelname}_samples_{idx}")
            count = cursor.fetchone()[0]
            if count == 0:
                return {"status": "error", "message": "APIConnectionError: Connection error."}

        elif dataset == "PandasEval":
            idx = find_available_index(cursor, f"PandasEval_{modelname}_samples")
            cursor.execute(f"CREATE TABLE PandasEval_{modelname}_samples_{idx} (id INT AUTO_INCREMENT PRIMARY KEY, task_id VARCHAR(255), completion LONGTEXT)")

            os.system(f"python datasets//PandasEval//PandasEval.py {base_url} {api_key} {model} {idx}")

            cursor.execute(f"SELECT COUNT(*) FROM PandasEval_{modelname}_samples_{idx}")
            count = cursor.fetchone()[0]
            if count == 0:
                return {"status": "error", "message": "APIConnectionError: Connection error."}

        elif dataset == "NumpyEval":
            idx = find_available_index(cursor, f"NumpyEval_{modelname}_samples")
            cursor.execute(f"CREATE TABLE NumpyEval_{modelname}_samples_{idx} (id INT AUTO_INCREMENT PRIMARY KEY, task_id VARCHAR(255), completion LONGTEXT)")

            os.system(f"python datasets//NumpyEval//NumpyEval.py {base_url} {api_key} {model} {idx}")

            cursor.execute(f"SELECT COUNT(*) FROM NumpyEval_{modelname}_samples_{idx}")
            count = cursor.fetchone()[0]
            if count == 0:
                return {"status": "error", "message": "APIConnectionError: Connection error."}

        elif dataset == "PanNumEval":
            idx = find_available_index(cursor, f"PanNumEval_{modelname}_samples")
            cursor.execute(f"CREATE TABLE PanNumEval_{modelname}_samples_{idx} (id INT AUTO_INCREMENT PRIMARY KEY, task_id VARCHAR(255), completion LONGTEXT)")

            os.system(f"python datasets//PanNumEval//PanNumEval.py {base_url} {api_key} {model} {idx}")

            cursor.execute(f"SELECT COUNT(*) FROM PanNumEval_{modelname}_samples_{idx}")
            count = cursor.fetchone()[0]
            if count == 0:
                return {"status": "error", "message": "APIConnectionError: Connection error."}

        elif dataset == "RustEvo":
            idx = find_available_index(cursor, f"RustEvo_{modelname}_results")
            cursor.execute(f"CREATE TABLE RustEvo_{modelname}_results_{idx} (id INT AUTO_INCREMENT PRIMARY KEY, task_id VARCHAR(255), completion LONGTEXT)")

            os.system(f"python datasets//RustEvo//Evaluate//eval_models.py {base_url} {api_key} {model} {idx}")

            cursor.execute(f"SELECT COUNT(*) FROM RustEvo_{modelname}_results_{idx}")
            count = cursor.fetchone()[0]
            if count == 0:
                return {"status": "error", "message": "APIConnectionError: Connection error."}

        elif dataset == "cruxeval":
            idx = find_available_index(cursor, f"cruxeval_{modelname}_results")
            cursor.execute(f"create TABLE cruxeval_{modelname}_results_{idx} (id INT AUTO_INCREMENT PRIMARY KEY, task_id VARCHAR(255), input longtext, output longtext, LLM_input longtext, LLM_output longtext, LLM_input_passed longtext, LLM_output_passed longtext)")

            os.system(f"python datasets//cruxeval//cruxeval.py {base_url} {api_key} {model} {idx}")

            cursor.execute(f"SELECT COUNT(*) FROM cruxeval_{modelname}_results_{idx}")
            count = cursor.fetchone()[0]
            if count == 0:
                return {"status": "error", "message": "APIConnectionError: Connection error."}

        elif dataset == "CodeApex":
            idx = find_available_index(cursor, f"CodeApex_{modelname}_results")
            cursor.execute(f"create TABLE CodeApex_{modelname}_results_{idx} (id INT AUTO_INCREMENT PRIMARY KEY, task_id VARCHAR(255), LLM_answer longtext, passed longtext)")

            os.system(f"python datasets//CodeApex//CodeApex.py {base_url} {api_key} {model} {idx}")

            cursor.execute(f"SELECT COUNT(*) FROM CodeApex_{modelname}_results_{idx}")
            count = cursor.fetchone()[0]
            if count == 0:
                return {"status": "error", "message": "APIConnectionError: Connection error."}

        else:
            save_directory = "datasets/CustomizedDataset"
            os.makedirs(save_directory, exist_ok=True)
            file_path = save_directory + "/" + f"{dataset}.jsonl"
            print(file_path)
            if not os.path.exists(file_path):
                return {"status": "error", "message": "不存在该数据集"}

            datasetname = dataset.replace(" ", "").replace("-", "").replace(".", "")
            idx = find_available_index(cursor, f"{datasetname}_{modelname}_samples")
            cursor.execute(f"CREATE TABLE {datasetname}_{modelname}_samples_{idx} (id INT AUTO_INCREMENT PRIMARY KEY, task_id VARCHAR(255), completion LONGTEXT)")

            os.system(f"python datasets//CustomizedDataset//CustomizedDataset.py {base_url} {api_key} {model} {idx} {dataset}")

            cursor.execute(f"SELECT COUNT(*) FROM {datasetname}_{modelname}_samples_{idx}")
            count = cursor.fetchone()[0]
            if count == 0:
                return {"status": "error", "message": "APIConnectionError: Connection error."}

        cursor.close()
        db.close()

# -------------------------------------------------------------------------------------------------------

        db = create_db_connection()
        cursor = db.cursor(DictCursor)
        if dataset == "human_eval" or dataset == "HumanEval":
            cursor.execute(f"SELECT * FROM human_eval_{modelname}_samples_{idx}_results")
        elif dataset == "PandasEval":
            cursor.execute(f"SELECT * FROM PandasEval_{modelname}_samples_{idx}_results")
        elif dataset == "NumpyEval":
            cursor.execute(f"SELECT * FROM NumpyEval_{modelname}_samples_{idx}_results")
        elif dataset == "PanNumEval":
            cursor.execute(f"SELECT * FROM PanNumEval_{modelname}_samples_{idx}_results")
        elif dataset == "RustEvo":
            cursor.execute(f"SELECT * FROM RustEvo_{modelname}_results_{idx}")
        elif dataset == "cruxeval":
            cursor.execute(f"SELECT * FROM cruxeval_{modelname}_results_{idx}")
        elif dataset == "CodeApex":
            cursor.execute(f"SELECT * FROM CodeApex_{modelname}_results_{idx}")
        else:
            datasetname = dataset.replace(" ", "").replace("-", "").replace(".", "")
            cursor.execute(f"SELECT * FROM {datasetname}_{modelname}_results_{idx}")

        rows = cursor.fetchall()
        json_data = json.dumps(rows, indent=4, default=str)

        cursor.close()
        db.close()

        return {"status": "success", "result": json_data}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/execute', methods=['POST'])
def handle_request():
    data = request.json
    required_params = ['api_key', 'base_url', 'model', 'dataset']

    if not all(param in data for param in required_params):
        return jsonify({"error": "缺少必要的参数"}), 400

    results = execute_dataset_logic(
        data['base_url'],
        data['api_key'],
        data['model'],
        data['dataset']
    )

    print(str(results))

    return jsonify(results)

@app.route('/upload', methods=['POST'])
def handle_upload():
    # 检查请求中是否包含文件
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "没有找到文件"}), 400

    # 获取上传的文件
    file = request.files['file']

    # 打印文件名
    print(f"收到的文件名: {file.filename}")

    # 检查文件扩展名是否为 .jsonl
    if not file.filename.endswith('.jsonl'):
        return jsonify({"status": "error", "message": "文件格式错误，请上传 .jsonl 文件"}), 400

    # 定义保存目录
    save_directory = "datasets/CustomizedDataset"

    # 确保目录存在
    os.makedirs(save_directory, exist_ok=True)

    # 检查同名文件是否存在
    file_path = os.path.join(save_directory, file.filename)
    if os.path.exists(file_path):
        return jsonify({"status": "error", "message": "存在同名数据集"}), 400

    try:
        # 创建临时文件路径用于校验
        temp_path = os.path.join(save_directory, f"temp_{file.filename}")
        file.save(temp_path)  # 先将文件保存到临时位置

        # 逐行读取文件内容并解析为 JSON
        with open(temp_path, 'r', encoding='utf-8') as f:
            for line_number, line in enumerate(f, start=1):
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    os.remove(temp_path)  # 删除临时文件
                    return jsonify({"status": "error", "message": f"第 {line_number} 行不是有效的 JSON 格式"}), 400

                # 检查 JSON 对象是否包含所需的字段
                required_fields = {"task_id", "prompt", "entry_point", "test"}
                if not required_fields.issubset(data.keys()):
                    os.remove(temp_path)  # 删除临时文件
                    return jsonify({"status": "error", "message": f"第 {line_number} 行缺少必要字段: {required_fields - data.keys()}"}), 400

        # 所有行校验通过后，重命名文件（正式保存）
        os.rename(temp_path, file_path)

    except Exception as e:
        print(f"文件处理错误: {e}")
        # 清理可能存在的临时文件
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return jsonify({"status": "error", "message": "文件处理失败"}), 500

    # 如果所有行都符合格式要求
    return jsonify({"status": "success", "message": "数据集上传成功"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)