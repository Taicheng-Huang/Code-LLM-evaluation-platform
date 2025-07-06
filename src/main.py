import pymysql
import os

base_url = "https://api.zetatechs.com/v1"
api_key = "sk-DhrVoQxgDb4BGiSUMJ91rhsiJhsvsPolI7lxxFT9iBrf3Te3"
# model = "deepseek-v3-250324" # 选择你要用的模型
model = "qwen-max-latest"
# model = "gpt-4.1-nano"
# model = "qwen3-235b-a22b"
# dataset = "human-eval"
# dataset = "PanNumEval"
# dataset = "NumpyEval"
# dataset = "PandasEval"
# dataset = "RustEvo"
dataset = "cruxeval"
# dataset = "CodeApex"

db = pymysql.connect(
    host='localhost',
    user='root',
    password='abc88668866', # 密码
    database='shixun', # 数据库
    autocommit=True
)
cursor = db.cursor()

if __name__ == '__main__':
    modelname = model.replace(" ", "").replace("-", "").replace(".","")
    if dataset == "human-eval":
        idx = 0
        for i in range(0,100):
            cursor.execute(f"select TABLE_NAME from INFORMATION_SCHEMA.TABLES where TABLE_SCHEMA='shixun' and TABLE_NAME='human_eval_{modelname}_samples_{i}';")
            results = cursor.fetchall()
            if len(results) == 0:
                cursor.execute(f"create TABLE human_eval_{modelname}_samples_{i} (id INT AUTO_INCREMENT PRIMARY KEY, task_id VARCHAR(255), completion longtext)")
                idx = i
                break
        os.system(f"python datasets//human_eval//get_samples.py {base_url} {api_key} {model} {idx}")
        os.system(f"python datasets//human_eval//get_results.py {base_url} {api_key} {model} {idx}")
    elif dataset == "PanNumEval":
        idx = 0
        for i in range(0,100):
            cursor.execute(f"select TABLE_NAME from INFORMATION_SCHEMA.TABLES where TABLE_SCHEMA='shixun' and TABLE_NAME='PanNumEval_{modelname}_samples_{i}';")
            results = cursor.fetchall()
            if len(results) == 0:
                cursor.execute(f"create TABLE PanNumEval_{modelname}_samples_{i} (id INT AUTO_INCREMENT PRIMARY KEY, task_id VARCHAR(255), completion longtext)")
                idx = i
                break
        os.system(f"python datasets//PanNumEval//PanNumEval.py {base_url} {api_key} {model} {idx}")
    elif dataset == "NumpyEval":
        idx = 0
        for i in range(0,100):
            cursor.execute(f"select TABLE_NAME from INFORMATION_SCHEMA.TABLES where TABLE_SCHEMA='shixun' and TABLE_NAME='NumpyEval_{modelname}_samples_{i}';")
            results = cursor.fetchall()
            if len(results) == 0:
                cursor.execute(f"create TABLE NumpyEval_{modelname}_samples_{i} (id INT AUTO_INCREMENT PRIMARY KEY, task_id VARCHAR(255), completion longtext)")
                idx = i
                break
        os.system(f"python datasets//NumpyEval//NumpyEval.py {base_url} {api_key} {model} {idx}")
    elif dataset == "PandasEval":
        idx = 0
        for i in range(0,100):
            cursor.execute(f"select TABLE_NAME from INFORMATION_SCHEMA.TABLES where TABLE_SCHEMA='shixun' and TABLE_NAME='PandasEval_{modelname}_samples_{i}';")
            results = cursor.fetchall()
            if len(results) == 0:
                cursor.execute(f"create TABLE PandasEval_{modelname}_samples_{i} (id INT AUTO_INCREMENT PRIMARY KEY, task_id VARCHAR(255), completion longtext)")
                idx = i
                break
        os.system(f"python datasets//PandasEval//PandasEval.py {base_url} {api_key} {model} {idx}")
    elif dataset == "RustEvo":
        idx = 0
        for i in range(0,100):
            cursor.execute(f"select TABLE_NAME from INFORMATION_SCHEMA.TABLES where TABLE_SCHEMA='shixun' and TABLE_NAME='RustEvo_{modelname}_results_{i}';")
            results = cursor.fetchall()
            if len(results) == 0:
                cursor.execute(f"create TABLE RustEvo_{modelname}_results_{i} (id INT AUTO_INCREMENT PRIMARY KEY, task_id VARCHAR(255), code_solution longtext, test_program longtext, result longtext)")
                idx = i
                break
        sql = f"INSERT INTO RustEvo_{modelname}_results_{idx} (task_id, code_solution, test_program, result) VALUES (%s, %s, %s, %s)"
        for i in range(0, 588):
            cursor.execute(sql, ("", "", "", ""))
        os.system(f"python datasets//RustEvo//Evaluate//eval_models.py {base_url} {api_key} {model} {idx}")
    elif dataset == "cruxeval":
        idx = 0
        for i in range(0,100):
            cursor.execute(f"select TABLE_NAME from INFORMATION_SCHEMA.TABLES where TABLE_SCHEMA='shixun' and TABLE_NAME='cruxeval_{modelname}_results_{i}';")
            results = cursor.fetchall()
            if len(results) == 0:
                cursor.execute(f"create TABLE cruxeval_{modelname}_results_{i} (id INT AUTO_INCREMENT PRIMARY KEY, task_id VARCHAR(255), input longtext, output longtext, LLM_input longtext, LLM_output longtext, LLM_input_passed longtext, LLM_output_passed longtext)")
                idx = i
                break
        os.system(f"python datasets//cruxeval//cruxeval.py {base_url} {api_key} {model} {idx}")
    elif dataset == "CodeApex":
        idx = 0
        for i in range(0,100):
            cursor.execute(f"select TABLE_NAME from INFORMATION_SCHEMA.TABLES where TABLE_SCHEMA='shixun' and TABLE_NAME='CodeApex_{modelname}_results_{i}';")
            results = cursor.fetchall()
            if len(results) == 0:
                cursor.execute(f"create TABLE CodeApex_{modelname}_results_{i} (id INT AUTO_INCREMENT PRIMARY KEY, task_id VARCHAR(255), LLM_answer longtext, passed longtext)")
                idx = i
                break
        os.system(f"python datasets//CodeApex//CodeApex.py {base_url} {api_key} {model} {idx}")

    # 关闭数据库连接
    db.close()