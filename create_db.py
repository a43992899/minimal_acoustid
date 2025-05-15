import os
import subprocess
import json
from multiprocessing import Pool
from functools import partial
from tqdm import tqdm

def find_audios(parent_dir, exts=None):
    """
    Recursively find all audio files within the parent directory with specified extensions.

    Args:
        parent_dir (str): The directory to search for audio files.
        exts (list, optional): List of file extensions to include. Defaults to common audio formats.

    Returns:
        list: A list of full paths to audio files.
    """
    if exts is None:
        exts = ['.wav', '.mp3', '.flac', '.webm', '.mp4', '.m4a']

    audio_files = []
    for root, dirs, files in os.walk(parent_dir):
        for file in files:
            if os.path.splitext(file)[1].lower() in exts:
                audio_files.append(os.path.join(root, file))
    return audio_files

def process_audio(audio_path, input_path, output_dir):
    """
    Process a single audio file using fpcalc and save the output to a JSON file.

    Args:
        audio_path (str): Path to the audio file.
        input_path (str): The original input path (could be dir or file).
        output_dir (str): Directory where JSON output files will be saved.

    Returns:
        str: The path of the processed audio file (for progress tracking).
    """
    try:
        # If input_path is a directory, we can form a relative path from it
        if os.path.isdir(input_path):
            relative_path = os.path.relpath(audio_path, input_path)
        else:
            # If input_path was a file (list), just use the filename for JSON output
            # or the entire path structure if you prefer
            relative_path = os.path.basename(audio_path)

        # Convert .wav -> .json (for example)
        json_relative_path = os.path.splitext(relative_path)[0] + '.json'
        json_path = os.path.join(output_dir, json_relative_path)

        # Skip if JSON already exists
        if os.path.exists(json_path):
            return audio_path
        
        # Run fpcalc
        result = subprocess.run(
            ['fpcalc', audio_path],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout

        # Parse the fpcalc output into a dictionary
        data = {}
        for line in output.strip().split('\n'):
            if '=' in line:
                key, value = line.split('=', 1)
                data[key] = value
        
        # update `ori_wav`
        data['ori_wav'] = audio_path

        # Ensure the output directory (and subfolders) exists
        os.makedirs(os.path.dirname(json_path), exist_ok=True)

        # Write the JSON data
        with open(json_path, 'w') as json_file:
            json.dump(data, json_file, indent=4)

        return audio_path
    except subprocess.CalledProcessError as e:
        print(f"Error processing {audio_path}: {e.stderr}")
    except Exception as e:
        print(f"Unexpected error processing {audio_path}: {e}")
    return None  # Return None if processing failed

def main():
    import argparse

    # Set up command-line argument parsing
    parser = argparse.ArgumentParser(
        description='Process audio files with fpcalc and save output to JSON.'
    )
    parser.add_argument(
        '--input',
        '-i',
        required=True,
        help='Path to either: (1) a directory of audio files, or (2) a text file listing audio paths.'
    )
    parser.add_argument(
        '--output_dir',
        '-o',
        required=True,
        help='Path to the output directory to save JSON files.'
    )
    parser.add_argument(
        "--processes",
        '-p',
        type=int,
        default=os.cpu_count(),
        help='Number of parallel processes to use. Defaults to the number of CPU cores.'
    )

    args = parser.parse_args()
    input_path = args.input
    output_dir = args.output_dir
    num_processes = args.processes

    audio_files = []

    if not os.path.exists(input_path):
        print(f"Error: The provided input path does not exist -> {input_path}")
        return

    # 1. If input is a file, treat it as a file list
    if os.path.isfile(input_path):
        with open(input_path, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        # Optionally filter only valid paths:
        audio_files = [line for line in lines if os.path.exists(line)]
    # 2. If input is a directory, search for audio files
    elif os.path.isdir(input_path):
        audio_files = find_audios(input_path)

    # Remove duplicates if any
    audio_files = list(set(audio_files))

    total_files = len(audio_files)
    print(f"Found {total_files} audio files to process.")

    if not audio_files:
        print("No audio files found. Exiting.")
        return

    # Create a partial function with fixed input_path and output_dir
    func = partial(
        process_audio,
        input_path=input_path,
        output_dir=output_dir
    )

    # Process files in parallel with a progress bar
    with Pool(processes=num_processes) as pool:
        for _ in tqdm(pool.imap_unordered(func, audio_files), total=total_files, desc="Processing Audio Files"):
            pass

    print("Processing complete.")

if __name__ == '__main__':
    main()
