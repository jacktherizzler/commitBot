import os
import subprocess
from getpass import getpass
import random
from datetime import datetime
import time
import requests

def run_command(command, repo_path=None):
    if repo_path:
        command = f"cd {repo_path} && {command}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    else:
        print(result.stdout)
        return True

def create_github_repo(token, repo_name):
    url = "https://api.github.com/user/repos"
    headers = {"Authorization": f"token {token}"}
    data = {"name": repo_name, "private": False}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 201:
        print(f"Repository {repo_name} created successfully.")
    elif response.status_code == 422 and "name already exists" in response.json()["errors"][0]["message"]:
        print(f"Repository {repo_name} already exists.")
    else:
        print(f"Error creating repository: {response.json()}")

def get_all_files(directory):
    file_list = []
    ignore_dirs = {'.git', '.github', '__pycache__', 'node_modules'}
    ignore_extensions = {'.pyc', '.pyo', '.pyd', '.db'}
    
    for root, dirs, files in os.walk(directory):
        # Remove ignored directories
        dirs[:] = [d for d in dirs if d not in ignore_dirs]
        
        for file in files:
            file_path = os.path.relpath(os.path.join(root, file), directory)
            _, ext = os.path.splitext(file)
            
            # Check if the file should be included
            if not file.startswith('.') and ext not in ignore_extensions:
                file_list.append(file_path)
    
    return file_list

def setup_repository(repo_url, project_directory):
    run_command("git init", project_directory)
    run_command("git checkout -b main", project_directory)
    run_command(f"git remote add origin {repo_url}", project_directory)
    
    # Create initial commit with README
    readme_path = os.path.join(project_directory, "README.md")
    with open(readme_path, "w") as f:
        f.write("# My GitHub Streak Project\n\nThis repository is used to maintain GitHub activity.")
    
    run_command("git add README.md", project_directory)
    run_command('git commit -m "Initial commit"', project_directory)
    success = run_command("git push -u origin main", project_directory)
    
    return success

github_username = input("Enter your GitHub username: ")
github_token = getpass("Enter your GitHub personal access token: ")
repo_name = input("Enter the name of your GitHub repository: ")

mode = int(input("Select mode (1 for regular commit, 2 for keeping GitHub streak): "))
file_frequency = "1day"
if mode == 1:
    file_frequency = input("Enter the file frequency (options: 30sec, 5min, 10min, 30min, 1hr, 6hrs, 1day): ")

project_directory = input("Enter the path to your project directory: ")

create_github_repo(github_token, repo_name)

repo_url = f"https://{github_token}@github.com/{github_username}/{repo_name}.git"

frequency_dict = {
    "30sec": 30,
    "5min": 300,
    "10min": 600,
    "30min": 1800,
    "1hr": 3600,
    "6hrs": 21600,
    "1day": 86400
}
frequency_seconds = frequency_dict.get(file_frequency, 86400)

def commit_and_push_files(repo_url, project_directory, frequency_seconds):
    if not setup_repository(repo_url, project_directory):
        print("Failed to set up the repository. Exiting.")
        return
    
    if mode == 1:
        files_to_commit = get_all_files(project_directory)
        if not files_to_commit:
            print("No files to commit. Exiting.")
            return
        
        random.shuffle(files_to_commit)
        
        for file in files_to_commit:
            run_command(f"git add {file}", project_directory)
            commit_message = f"Add {file} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            run_command(f'git commit -m "{commit_message}"', project_directory)
            if run_command("git push origin main", project_directory):
                print(f"Committed and pushed {file} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                print(f"Failed to push {file}")
            
            time.sleep(frequency_seconds)
        
        print("All files have been committed and pushed. Exiting.")
    elif mode == 2:
        readme_path = os.path.join(project_directory, "README.md")
        with open(readme_path, "a") as f:
            f.write(f"\nUpdate on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        run_command("git add README.md", project_directory)
        commit_message = f"Keep GitHub streak active - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        run_command(f'git commit -m "{commit_message}"', project_directory)
        if run_command("git push origin main", project_directory):
            print(f"Committed and pushed README update at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("Failed to push README update")
        
        print("README has been updated. Exiting.")

commit_and_push_files(repo_url, project_directory, frequency_seconds)
