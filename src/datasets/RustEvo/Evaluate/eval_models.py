import sys
from unit import call_LLM, run_rust_code,get_test_program_prompt,get_code_solution_prompt,extract_rust_code
import json
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
import os
import re
from src import main


def needs_testing(entry: Dict[str, Any], model: str) -> bool:
    """Check if processing is required for the given model."""
    code_solution_key = f"{model}_code_solution"
    test_program_key = f"{model}_test_program"
    result_key = f"{model}_result"
    # TODO return not entry.get(code_solution_key) or not entry.get(test_program_key) or not entry.get(result_key)
    return 1

def initialize_model_fields(entry: Dict[str, Any], model) -> None:
    """Ensure each model's fields are initialized explicitly."""
    # for model in MODELS:
    for suffix in ['code_solution', 'test_program', 'result']:
        entry.setdefault(f"{model}_{suffix}", '')

def process_model(entry: Dict[str, Any], model: str, api_key: str, base_url: str) -> None:
    """Process a single model (baseline only) sequentially."""
    query = entry.get('query', '')
    signature = entry.get('signature', '')
    api_info = entry.get('api_info', '')
    api = entry.get('api', '')

    # Generate code solution
    raw_code_solution = call_LLM(
        get_code_solution_prompt(query, signature, api_info),
        model, api_key, base_url
    )

    code_solution = extract_rust_code(raw_code_solution)
    entry[f"{model}_code_solution"] = code_solution

    # Generate test program
    raw_test_program = call_LLM(
        get_test_program_prompt(query, code_solution, api),
        model, api_key, base_url
    )

    test_program = extract_rust_code(raw_test_program)
    entry[f"{model}_test_program"] = test_program

    # Execute test program
    try:
        print(str(entry["task_idx"]))
        entry[f"{model}_result"] = run_rust_code(test_program)
    except Exception as e:
        entry[f"{model}_result"] = f"Execution error: {str(e)}"

def process_entry(entry: Dict[str, Any], api_key: str, base_url: str, model) -> Dict[str, Any]:
    """Process all models sequentially within each entry."""
    initialize_model_fields(entry, model)

    if needs_testing(entry, model):
        process_model(entry, model, api_key, base_url)

    return entry

if __name__ == "__main__":
    base_url = sys.argv[1]
    api_key = sys.argv[2]
    model = sys.argv[3]
    index = sys.argv[4]

    with open("datasets//RustEvo//Evaluate//example.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    total_entries = len(data)

    # Adjust batch size as appropriate for your hardware/API limits
    batch_size = 100

    with tqdm(total=total_entries, desc="Overall Progress") as overall_pbar:
        for batch_start in range(0, total_entries, batch_size):
            batch_end = min(batch_start + batch_size, total_entries)
            current_batch = data[batch_start:batch_end]

            with ThreadPoolExecutor(max_workers=batch_size) as executor:
                futures = {
                    executor.submit(process_entry, entry, api_key, base_url, model): idx
                    for idx, entry in enumerate(current_batch, start=batch_start)
                }

                for future in as_completed(futures):
                    idx = futures[future]
                    try:
                        data[idx] = future.result()
                    except Exception as e:
                        tqdm.write(f"Error processing entry {idx}: {str(e)}")
                    finally:
                        overall_pbar.update(1)

    modelname = model.replace(" ", "").replace("-", "").replace(".", "")
    sql = f"UPDATE RustEvo_{modelname}_results_{index} set task_id = %s, code_solution = %s, test_program = %s, result = %s where id = %s"
    for i in range(0, 588):
        # main.cursor.execute(sql, ("RustEvo/" + str(data[i]["task_idx"]), str(data[i][f"{model}_code_solution"]), str(data[i][f"{model}_test_program"]), str(data[i][f"{model}_result"]), str(data[i]["task_idx"])))
        main.cursor.execute(sql, ("RustEvo/" + str(data[i]["task_idx"]), str(data[i][f"{model}_code_solution"]),
                                  str(data[i][f"{model}_test_program"]), str(data[i][f"{model}_result"]),
                                  str(data[i]["task_idx"])))