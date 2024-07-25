import torch
import pandas as pd
from llama import Llama
import hydra
from omegaconf import DictConfig
import time
import re
import ast
import os

PROJECT_ROOT = os.path.abspath(os.path.join(__file__, '../../../'))

def save_checkpoint(data, file_path, mode='a'):
    """ Helper function to save data to a CSV file """
    df = pd.DataFrame(data, columns=['text', 'gt', 'topics'])
    df.to_csv(file_path, mode=mode, header=mode=='w', index=False)
    print(f'Saved checkpoint to {file_path}')

@hydra.main(config_path="../../cfg", config_name="config", version_base='1.3.2')
def main(cfg: DictConfig):
    ckpt_dir = os.path.join(PROJECT_ROOT, "models/llama3/Meta-Llama-3-8B-Instruct/")
    tokenizer_path = os.path.join(PROJECT_ROOT, "models/llama3/Meta-Llama-3-8B-Instruct/tokenizer.model")
    temperature = 0
    top_p = 0.9
    max_seq_len = 1024
    max_batch_size = 2
    max_gen_len = None

    print('building generator')

    generator = Llama.build(
        ckpt_dir=ckpt_dir,
        tokenizer_path=tokenizer_path,
        max_seq_len=max_seq_len,
        max_batch_size=max_batch_size,
    )

    datetime = time.strftime("%Y_%m_%d-%H_%M_%S")
    output_dir = os.path.join(PROJECT_ROOT, cfg.outputs.path, cfg.llm.model, datetime)
    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(os.path.join(PROJECT_ROOT, cfg.data.multilabel))
    df = df.iloc[:10]

    with open(os.path.join(PROJECT_ROOT, cfg.llm.promts, cfg.llm.model, 'multilabel', cfg.llm.system_prompt), 'r') as f:
        system_prompt = f.read()

    with open(os.path.join(PROJECT_ROOT, cfg.llm.promts, cfg.llm.model, 'multilabel', cfg.llm.user_prompt), 'r') as f:
        user_prompt = f.read()

    start_index = 0
    checkpoint_path = os.path.join(output_dir, 'checkpoint.csv')

    if os.path.exists(checkpoint_path):
        checkpoint_df = pd.read_csv(checkpoint_path)
        start_index = len(checkpoint_df)
        print(f"Resuming from index {start_index}")

    topics = cfg.labels.topics
    print(f'Topics list: {topics}')
    num_topics = len(topics)
    print(f'Num topics: {num_topics}')

    total_time = 0
    batch_data = []
    topic_pattern = re.compile(r'\["[^"]*"(?:, "[^"]*")*\]')

    for topics_num in range(1, num_topics+1):
        num_topics_chunks = num_topics // topics_num
        remainder = num_topics % topics_num
        topics_chunks = [topics[i*topics_num:(i+1)*topics_num] for i in range(num_topics_chunks)]
        if remainder:
            topics_chunks.append(topics[num_topics_chunks*topics_num:])

        checkpoint_path = os.path.join(output_dir, f'{topics_num}_topics.json')
        batch_data = []

        for idx, row in df.iterrows():
            data = row['text']
            gt = row['topics']
            full_scores = {}

            for topics_chunk in topics_chunks:
                dialog = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt.format(data=data, labels_list=", ".join(topics_chunk))}
                ]

                try:
                    results = generator.chat_completion(
                        [dialog],
                        max_gen_len=max_gen_len,
                        temperature=temperature,
                        top_p=top_p,
                    )

                    generation_content = results[0]['generation']['content']

                    try:
                        scores = ast.literal_eval(generation_content)
                        if isinstance(scores, dict):
                            filtered_scores = {k: v for k, v in scores.items() if k in topics_chunk}
                            full_scores.update(filtered_scores)
                            print(f'Processed {len(filtered_scores)}: {filtered_scores}')
                        else:
                            print(f"Format error: {scores}")
                            scores = {"format_error": 0.0}
                    except ValueError:
                        print(f"Value error: {scores}")

                except Exception as e:
                    print(f"Results generation error: {e}")
                    print(generation_content)
                    scores = {"gen_error": 0.0}

            batch_data.append([data, gt, full_scores])
        save_checkpoint(batch_data, checkpoint_path)
        batch_data = []

    batch_data = []

    print("Data labeling complete and files saved")

if __name__ == "__main__":
    import sys
    print('executing')
    hydra.main(config_path="../../cfg", config_name="config", version_base='1.3.2')(main)