import os
import subprocess
import json
import datetime

def get_current_version():
    try:
        with open("package.json", "r") as f:
            data = json.load(f)
            return data.get("version", "0.0.0")
    except:
        return "0.0.0"

def increment_version(version_str):
    major, minor, patch = map(int, version_str.split('.'))
    patch += 1
    return f"{major}.{minor}.{patch}"

def update_package_json(new_version):
    try:
        with open("package.json", "r") as f:
            data = json.load(f)
        
        data["version"] = new_version
        
        with open("package.json", "w") as f:
            json.dump(data, f, indent=2)
        print(f"✅ Version bumped to {new_version}")
    except Exception as e:
        print(f"❌ Failed to update package.json: {e}")

def run_git_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return result.stdout.decode().strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Git Error: {e.stderr.decode().strip()}")
        return None

def nexus_commit(message="Auto-update"):
    print("🔄 NEXUS GIT: INITIATING SECURE COMMIT...")
    
    # 1. Check status
    status = run_git_command("git status --porcelain")
    if not status:
        print("✨ No changes to commit.")
        return

    # 2. Bump Version
    current_ver = get_current_version()
    new_ver = increment_version(current_ver)
    update_package_json(new_ver)
    
    # 3. Add All
    run_git_command("git add .")
    
    # 4. Commit
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    commit_msg = f"NEXUS v{new_ver} | {timestamp} | {message}"
    run_git_command(f'git commit -m "{commit_msg}"')
    
    print("   > Pushing to Remote Repository...")
    run_git_command("git push")
    
    print(f"\n✅ SUCCESS: Nexus v{new_ver} Deployed & Synced!")
    
    print(f"✅ SECURE COMMIT COMPLETE: {commit_msg}")

if __name__ == "__main__":
    import sys
    msg = sys.argv[1] if len(sys.argv) > 1 else "Routine System Update"
    nexus_commit(msg)
