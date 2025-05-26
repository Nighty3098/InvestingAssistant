import os
import subprocess


def format_python_files(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                print(f"Formatting: {file_path}")
                subprocess.run(["black", file_path])


if __name__ == "__main__":
    project_directory = "."
    format_python_files(project_directory)
