import subprocess
import os
import sys

def execute_gradle_obfuscation(output_dir_name, mode):
    """Runs the Gradle obfuscation task with a specific mode and output directory."""
    try:
        print(f"Starting Gradle obfuscation task for mode '{mode}', output: 'build/{output_dir_name}'...")
        if not os.access("./gradlew", os.X_OK):
            os.chmod("./gradlew", 0o755)

        obfuscator_args_string = f"src/main/java build/{output_dir_name} {mode}"
        command = ["./gradlew", "spoonObfuscate", f"--args={obfuscator_args_string}", "--console=plain"]

        print(f"Executing command: {' '.join(command)}")

        process = subprocess.run(command, capture_output=True, text=True, check=False) # check=False to handle output manually

        print(f"Gradle task for mode '{mode}' completed.")
        sys.stdout.write("stdout:\n" + process.stdout + "\n")
        if process.stderr:
            sys.stderr.write("stderr:\n" + process.stderr + "\n")

        if process.returncode != 0:
            print(f"Error: Gradle task for mode '{mode}' failed with return code {process.returncode}.")
            return False
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error during obfuscation for mode '{mode}': {e}")
        sys.stdout.write("stdout:\n" + e.stdout + "\n")
        sys.stderr.write("stderr:\n" + e.stderr + "\n")
        return False
    except FileNotFoundError:
        print("Error: gradlew not found. Make sure you are in the project root directory.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during obfuscation for mode '{mode}': {e}")
        return False

def display_obfuscated_file(output_dir_name, relative_file_path="source/Main.java"):
    """Prints the content of a specific obfuscated Java file."""
    obfuscated_file_path_host = os.path.join("build", output_dir_name, relative_file_path)

    base_path = "/app" if os.path.exists("/.dockerenv") else "."
    obfuscated_file_path_actual = os.path.join(base_path, "build", output_dir_name, relative_file_path)

    try:
        print(f"\nReading obfuscated file: {obfuscated_file_path_actual} (host path: {obfuscated_file_path_host})")
        with open(obfuscated_file_path_actual, 'r') as f:
            content = f.read()
            mode_name = output_dir_name.replace('obfuscated-source-', '')
            print(f"\n--- Obfuscated {relative_file_path} (mode: {mode_name}) ---")
            print(content)
            print(f"--- End of Obfuscated {relative_file_path} (mode: {mode_name}) ---")
    except FileNotFoundError:
        print(f"Error: Obfuscated file not found at {obfuscated_file_path_actual}")
    except Exception as e:
        print(f"Error reading obfuscated file {obfuscated_file_path_actual}: {e}")

if __name__ == "__main__":
    print("\n--- Starting 'bodies' obfuscation (name changes + body removal) ---")
    if execute_gradle_obfuscation("obfuscated-source-bodies", "bodies"):
        display_obfuscated_file("obfuscated-source-bodies", "source/Main.java")
    else:
        print("Obfuscation process for 'bodies' failed. Skipping printing of obfuscated file.")

    print("\n\n--- Starting 'names' obfuscation (method and variable name changes) ---")
    if execute_gradle_obfuscation("obfuscated-source-names", "names"):
        display_obfuscated_file("obfuscated-source-names", "source/Main.java")
    else:
        print("Obfuscation process for 'names' failed. Skipping printing of obfuscated file.")
