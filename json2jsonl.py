import os, json, sys, argparse
from tqdm import tqdm

def find_filelist(fp_path, ext=".json"):
    filelist = []
    for root, dirs, files in os.walk(fp_path):
        for file in files:
            if file.endswith(ext):
                filelist.append(os.path.join(root, file))
    return filelist

def load_json(path):
    with open(path, "r") as f:
        d = json.load(f)
        # add json file path to the dict
        d["PATH"] = path
    return d

def save_jsonl(data, path):
    with open(path, "w") as f:
        for item in data:
            f.write(json.dumps(item) + "\n")

argparser = argparse.ArgumentParser()
argparser.add_argument("--input_json_parent_dir", '-i', type=str, required=True)
argparser.add_argument("--output_jsonl_path", '-o', type=str, required=True)
args = argparser.parse_args()

input_json_parent_dir = args.input_json_parent_dir
output_jsonl_path = args.output_jsonl_path

json_files = find_filelist(input_json_parent_dir)
print(f"Found {len(json_files)} json files in {input_json_parent_dir}")


data = []
for j in tqdm(json_files):
    try:
        data.append(load_json(j))
    except Exception as e:
        print(f"Failed to load {j}. Error: {e}")
        
save_jsonl(data, output_jsonl_path)
print(f"Saved {len(data)} items to {output_jsonl_path}")

# python json2jsonl.py -i /aifs4su/mmdata/rawdata/codeclm/music/harmonix_Youtube_songs_fp/ -o ./harmonix_fp.jsonl