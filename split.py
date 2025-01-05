# SPLIT! - A simple video splitter with ffmpeg.
# Hand-crafted with love by jepgambardella.
# Che cosa avete contro la nostalgia, eh? È l'unico svago che resta per chi è diffidente verso il futuro, l'unico.


import sys
import importlib.util
import shutil
import subprocess
import math
import os
import re

# ----- CHECKS SECTION -----
MIN_PYTHON = (3, 7)  #Python 3.7 or higher

def check_python_version():
    #Ensure Python version >= MIN_PYTHON.
    if sys.version_info < MIN_PYTHON:
        print(f"ERROR: Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or higher is required.")
        sys.exit(1)

def check_module_installed(module_name):

    #Check if a Python module is installed. If not, exit.
    
    spec = importlib.util.find_spec(module_name)
    if spec is None:
        print(f"ERROR: The Python module '{module_name}' is not installed.")
        print("Please install it via:")
        print(f"    pip install {module_name}")
        sys.exit(1)

def check_ffmpeg_installed():
    #Check if 'ffmpeg' and 'ffprobe' are available in the system PATH
    ffmpeg_path = shutil.which("ffmpeg")
    ffprobe_path = shutil.which("ffprobe")
    if not ffmpeg_path or not ffprobe_path:
        print("ERROR: 'ffmpeg' or 'ffprobe' not found in PATH.")
        print("Please install ffmpeg or make sure it's in your PATH.")
        sys.exit(1)

def check_requirements():
    
    check_python_version()
    check_ffmpeg_installed()
# ----- END CHECKS SECTION -----


WHITE = "\033[37m"
GREEN = "\033[32m"
RED = "\033[31m"
RESET = "\033[0m"

def print_colored_menu(lines):

    for i, line in enumerate(lines):
        if i == 0:
            print(f"{WHITE}{line}{RESET}")
        else:
            if i % 2 == 1:
                print(f"{GREEN}{line}{RESET}")
            else:
                print(f"{RED}{line}{RESET}")

def colored_input(prompt):
    """Input prompt in white color."""
    return input(f"{WHITE}{prompt}{RESET}").strip()

def parse_time_intuitive(timestr):
    """
    Parses strings like '10s', '10m10s', '2h', or just '10'.
    Returns total seconds as float.
    """
    timestr = timestr.strip().lower()
    if timestr.isdigit():
        timestr += "s"
    pattern = r'^(?:(?P<hours>\d+)h)?(?:(?P<minutes>\d+)m)?(?:(?P<seconds>\d+)s)?$'
    match = re.match(pattern, timestr)
    if not match:
        raise ValueError(f"Invalid time format: {timestr}")
    hours = int(match.group('hours') or 0)
    minutes = int(match.group('minutes') or 0)
    seconds = int(match.group('seconds') or 0)
    return float(hours * 3600 + minutes * 60 + seconds)

def show_available_formats():
    """
    Runs 'ffmpeg -hide_banner -loglevel error -formats' and shows raw output.
    """
    print("\nShowing all available formats from ffmpeg:\n")
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-formats"]
    subprocess.run(cmd)
    print("\n--- End of format list ---\n")

def seconds_to_hhmmss(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = seconds % 60
    return f"{h:02d}:{m:02d}:{s:05.2f}"

def get_video_duration(video_path):
    if not os.path.isfile(video_path):
        print("File does not exist.")
        return None
    try:
        cmd_duration = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            video_path
        ]
        result = subprocess.run(cmd_duration, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print("Error getting duration:", e)
        return None

def perform_split_fast(video_path, start_time, chunk_duration, output_filename):
    cmd_split = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-i", video_path,
        "-ss", str(start_time),
        "-t", str(chunk_duration),
        "-c", "copy",
        output_filename
    ]
    subprocess.run(cmd_split, check=True)

def perform_split_encode(video_path, start_time, chunk_duration, output_filename, out_format=None):
    cmd_split = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-y",
        "-ss", str(start_time),
        "-t", str(chunk_duration),
        "-i", video_path
    ]
    if out_format is not None:
        ext = f".{out_format}"
        if not output_filename.endswith(ext):
            base, _ = os.path.splitext(output_filename)
            output_filename = base + ext
    cmd_split += [output_filename]
    subprocess.run(cmd_split, check=True)

def choose_mode_and_format(video_path):
    """
    Ask if user wants fast (copy) or precise (re-encode).
    Also allow to keep same or choose different format,
    or go back to main menu.
    """
    while True:
        lines = [
            "Choose splitting mode:",
            "1) Fast mode (no re-encoding)",
            "2) Precise mode (re-encoding, might take more time)",
        ]
        print_colored_menu(lines)
        
        mode_choice = colored_input("Option: ")
        
        if mode_choice == "1":
            return {
                'mode': 'fast',
                'format': None,
                'back': False,
                'to_menu': False
            }
        elif mode_choice == "2":
            while True:
                lines_sub = [
                    "Choose re-encode option:",
                    "1) Keep same format",
                    "2) Choose a different format",
                    "3) Go back (change mode)",
                    "4) Go to main menu"
                ]
                print_colored_menu(lines_sub)
                
                encode_choice = colored_input("Option: ")
                
                if encode_choice == "1":
                    base, ext = os.path.splitext(video_path)
                    container = ext.replace('.', '')
                    if container == '':
                        container = None
                    return {
                        'mode': 'encode',
                        'format': container,
                        'back': False,
                        'to_menu': False
                    }
                elif encode_choice == "2":
                    while True:
                        lines_format = [
                            "Choose a new format extension (e.g. mp4, mkv, mov).",
                            "(Type '1' to see the raw formats from ffmpeg.)"
                        ]
                        print_colored_menu(lines_format)
                        
                        new_format = colored_input("Your choice: ")
                        if new_format == "1":
                            show_available_formats()
                            continue
                        if len(new_format) == 0:
                            print("Invalid format, try again.")
                            continue
                        return {
                            'mode': 'encode',
                            'format': new_format,
                            'back': False,
                            'to_menu': False
                        }
                elif encode_choice == "3":
                    return {
                        'mode': None,
                        'format': None,
                        'back': True,
                        'to_menu': False
                    }
                elif encode_choice == "4":
                    return {
                        'mode': None,
                        'format': None,
                        'back': False,
                        'to_menu': True
                    }
                else:
                    print("Invalid choice, try again.")
        else:
            print("Invalid choice, try again.")

def operation_divide_equal_parts(video_path, total_duration):
    """Splits the video into N equal parts."""
    try:
        num_parts = int(colored_input("How many parts? "))
        if num_parts <= 0:
            raise ValueError
    except ValueError:
        print("Invalid number of parts.")
        return False
    
    chunk_duration = total_duration / num_parts
    last_chunk_duration = total_duration - chunk_duration * (num_parts - 1)
    
    if abs(last_chunk_duration - chunk_duration) < 0.01:
        print(f"\nRecap: {num_parts} parts, each ~ {seconds_to_hhmmss(chunk_duration)}.")
    else:
        print(
            f"\nRecap: {num_parts - 1} parts of ~ {seconds_to_hhmmss(chunk_duration)} "
            f"and 1 part of {seconds_to_hhmmss(last_chunk_duration)}."
        )
    
    while True:
        result_mode = choose_mode_and_format(video_path)
        if result_mode['to_menu']:
            print("Returning to main menu...")
            return False
        if result_mode['back']:
            continue
        
        chosen_mode = result_mode['mode']
        chosen_format = result_mode['format']
        break
    
    confirm = colored_input("Proceed with splitting? [s/N]: ").lower()
    if confirm not in ["s", "si"]:
        print("Operation canceled.")
        return False
    
    base_name, extension = os.path.splitext(os.path.basename(video_path))
    print("\nSplitting...\n")
    
    for i in range(num_parts):
        start_time = i * chunk_duration
        output_filename = f"{base_name}_{i+1}{extension}"
        
        if chosen_mode == 'fast':
            print(f"{GREEN}Processing \"{output_filename}\" (fast mode)...{RESET}")
            perform_split_fast(video_path, start_time, chunk_duration, output_filename)
        else:
            print(f"{RED}Processing \"{output_filename}\" (precise mode)...{RESET}")
            perform_split_encode(video_path, start_time, chunk_duration, output_filename, out_format=chosen_format)
    
    print("\nDone!\n")
    return True

def operation_divide_fixed_length(video_path, total_duration):
    """Splits the video into multiple clips of a user-defined length (intuitive)."""
    while True:
        time_str = colored_input("Clip length (e.g. 10s, 2m, 1m30s, or just '10'): ")
        try:
            chunk_duration = parse_time_intuitive(time_str)
            if chunk_duration <= 0:
                raise ValueError
            break
        except ValueError:
            print("Invalid format. Try e.g. '10s', '2m', '1m30s', '1h'...\n")
    
    num_chunks = math.ceil(total_duration / chunk_duration)
    last_chunk_duration = total_duration % chunk_duration
    
    if abs(last_chunk_duration) < 0.01:
        print(f"\nRecap: {num_chunks} clips, each ~ {seconds_to_hhmmss(chunk_duration)}.")
    else:
        print(
            f"\nRecap: {num_chunks - 1} clips of {seconds_to_hhmmss(chunk_duration)} "
            f"and 1 clip of {seconds_to_hhmmss(last_chunk_duration)}."
        )
    
    while True:
        result_mode = choose_mode_and_format(video_path)
        if result_mode['to_menu']:
            print("Returning to main menu...")
            return False
        if result_mode['back']:
            continue
        
        chosen_mode = result_mode['mode']
        chosen_format = result_mode['format']
        break
    
    confirm = colored_input("Proceed with splitting? [s/N]: ").lower()
    if confirm not in ["s", "si"]:
        print("Operation canceled.")
        return False
    
    base_name, extension = os.path.splitext(os.path.basename(video_path))
    print("\nSplitting...\n")
    
    for i in range(num_chunks):
        start_time = i * chunk_duration
        output_filename = f"{base_name}_{i+1}{extension}"
        
        if chosen_mode == 'fast':
            print(f"{GREEN}Processing \"{output_filename}\" (fast mode)...{RESET}")
            perform_split_fast(video_path, start_time, chunk_duration, output_filename)
        else:
            print(f"{RED}Processing \"{output_filename}\" (precise mode)...{RESET}")
            perform_split_encode(video_path, start_time, chunk_duration, output_filename, out_format=chosen_format)
    
    print("\nDone!\n")
    return True

def show_heading():
    big_title = f"""{RED}
  ___  ___  _     ___  _____  _ 
 / __|| _ \| |   |_ _||_   _|| |
 \__ \|  _/| |__  | |   | |  |_|
 |___/|_|  |____||___|  |_|  (_){RESET}
"""
    print(big_title)
    print(f"{WHITE}SPLIT! - A script to split videos with ffmpeg.{RESET}")
    print(f"hand-crafted by {RED}jepgambardella{RESET}\n")
    print("\"Io non volevo solo partecipare alle feste, volevo avere il potere di farle fallire\".\n")

def main():
    # 1) Check requirements before doing anything else
    check_requirements()
    
    while True:
        show_heading()
        lines_main = [
            "Choose an option:",
            "1 - Split into equal chunks",
            "2 - Split in timeranges",
            "3 - Quit"
        ]
        print_colored_menu(lines_main)
        
        choice = colored_input("Option: ")
        
        if choice == "3":
            print("Thanks, hope to see you again!")
            break
        
        elif choice in ["1", "2"]:
            video_path = colored_input("\nEnter the path of the video file: ")
            total_duration = get_video_duration(video_path)
            if total_duration is None:
                continue
            
            print(f"Total video duration: {total_duration:.2f}s ({seconds_to_hhmmss(total_duration)})\n")
            
            while True:
                if choice == "1":
                    success = operation_divide_equal_parts(video_path, total_duration)
                else:
                    success = operation_divide_fixed_length(video_path, total_duration)
                
                if not success:
                    break
                
                lines_sub = [
                    "Choose:",
                    "1) Elaborate the same file",
                    "2) Go back to the main menu"
                ]
                print_colored_menu(lines_sub)
                
                post_choice = colored_input("Option: ")
                
                if post_choice == "1":
                    while True:
                        lines_sub2 = [
                            "Choose an option:",
                            "1 - Split into equal chunks",
                            "2 - Split in timeranges",
                        ]
                        print_colored_menu(lines_sub2)
                        
                        sub_choice = colored_input("Option: ")
                        if sub_choice not in ["1", "2"]:
                            print("Please make a valid choice.")
                            continue
                        else:
                            choice = sub_choice
                            break
                    continue
                else:
                    break
        else:
            print("Invalid choice. Try again.")
            continue

if __name__ == "__main__":
    main()

# È così triste essere bravi: si rischia di diventare abili.