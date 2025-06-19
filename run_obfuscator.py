import subprocess
import os
import sys
import requests
import json
import re

# --- Constants for Ollama API ---
OLLAMA_API_URL = "http://rhaegal.dimis.fim.uni-passau.de:15343/api/generate"
OLLAMA_MODEL_NAME = "codellama:7b"

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

def get_and_print_code(file_path_from_project_root, description):
    """Reads, prints, and returns the content of a specific source file."""
    base_path = "/app" if os.path.exists("/.dockerenv") else "."
    actual_file_path = os.path.join(base_path, file_path_from_project_root)
    content = None
    try:
        print(f"\nReading {description} file: {actual_file_path}")
        with open(actual_file_path, 'r') as f:
            content = f.read()
            print(f"\n--- {description} {os.path.basename(file_path_from_project_root)} ---")
            print(content)
            print(f"--- End of {description} {os.path.basename(file_path_from_project_root)} ---")
    except FileNotFoundError:
        print(f"Error: {description} file not found at {actual_file_path}")
    except Exception as e:
        print(f"Error reading {description} file {actual_file_path}: {e}")
    return content

def generate_tests_with_llm(java_code_string, code_description):
    """Sends Java code to the Ollama API and prints the generated JUnit tests."""
    if not java_code_string:
        print(f"No Java code provided for '{code_description}'. Skipping test generation.")
        return None

    print(f"\n--- Requesting JUnit tests from LLM for: {code_description} ---")
    print(f"(Using model: {OLLAMA_MODEL_NAME} at {OLLAMA_API_URL}))")
    print("Please ensure you are connected to the university VPN.")

    class_name = "UnknownClass"
    try:
        lines = java_code_string.splitlines()
        for line in lines:
            if "public class" in line:
                class_name = line.split("public class")[1].split("{")[0].strip()
                break
    except Exception:
        pass

    prompt = f'''You are an expert Java software developer specializing in writing comprehensive unit tests.
        Your task is to generate a complete JUnit 5 test class for the provided Java code.
        Instructions:
        1. The test class should be fully self-contained and ready to compile.
        2. Include all necessary imports for JUnit 5 (e.g., `import org.junit.jupiter.api.*;`, `import static org.junit.jupiter.api.Assertions.*;`).
        3. Generate test methods for all public methods in the provided code. If the main method is the primary entry point for logic, include tests for its behavior or the methods it calls.
        4. For methods with non-void return types, include assertions (e.g., `assertEquals`, `assertTrue`, `assertFalse`, `assertNotNull`, `assertThrows`) to check for expected outcomes. You may need to infer reasonable inputs and expected outputs based on the method's logic or name.
        5. For void methods, try to test their behavior by checking for expected side effects if possible (though this might be hard without more context or mocking capabilities). At a minimum, ensure they can be called without throwing unexpected exceptions for basic valid inputs.
        6. Name the test class "LLMGenerated{class_name}Test" to avoid conflicts with existing test classes.
        7. Pay attention to constructors and how objects of the class should be instantiated for testing.
        8. Handle potential exceptions thrown by the methods under test using `assertThrows` where appropriate.
        9. If a method is instance-based (non-static), make sure to create an instance of the class before calling the method.
        10. IMPORTANT: Provide only the Java code without any additional text or code fences. Do not include ```java or ``` markers, or any explanatory text.

        The Java code to test is as follows:
        ```java
        {java_code_string}
        ```

        Provide only the Java code for the test class.
        '''

    payload = {
        "model": OLLAMA_MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=180)
        response.raise_for_status()

        response_data = response.json()
        generated_test_code = response_data.get("response", "Error: No response field in LLM output.")

        # Clean up the response to extract only the Java code
        cleaned_code = clean_generated_code(generated_test_code)

        print(f"\n--- Generated JUnit Tests for: {code_description} ---")
        print(cleaned_code)
        print(f"--- End of Generated Tests for: {code_description} ---")

        return cleaned_code

    except requests.exceptions.ConnectionError as e:
        print(f"Error connecting to Ollama API at {OLLAMA_API_URL}.")
        print("Please ensure the API is reachable and you are connected to the university VPN.")
        print(f"Details: {e}")
    except requests.exceptions.Timeout as e:
        print(f"Request to Ollama API timed out after 180 seconds.")
        print(f"Details: {e}")
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error occurred while communicating with Ollama API: {e.response.status_code} {e.response.reason}")
        print(f"Response body: {e.response.text}")
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response from Ollama API.")
        print(f"Response text: {response.text if 'response' in locals() else 'No response object'}")
        print(f"Details: {e}")
    except Exception as e:
        print(f"An unexpected error occurred while generating tests with LLM: {e}")

    return None

def clean_generated_code(code_text):
    """Clean up the LLM-generated code by removing markdown and explanatory text."""
    # Remove markdown code blocks
    code_text = re.sub(r'^```java\s*', '', code_text, flags=re.MULTILINE)
    code_text = re.sub(r'^```\s*', '', code_text, flags=re.MULTILINE)

    # Remove lines that don't look like Java code
    java_lines = []
    in_java_block = False

    for line in code_text.splitlines():
        # Skip explanatory text at the beginning
        if not in_java_block:
            if line.strip().startswith("package ") or line.strip().startswith("import ") or "class " in line:
                in_java_block = True
                java_lines.append(line)
            continue

        # Skip explanatory text at the end
        if line.strip().startswith("Note:") or line.strip().startswith("Here is") or line.strip() == "":
            continue

        java_lines.append(line)

    # If we couldn't find the start of Java code, return the original with just code fence cleanup
    if not java_lines and code_text.strip():
        return code_text

    return "\n".join(java_lines)

def save_test_to_file(test_code, test_file_path):
    """Saves the generated test code to a file."""
    try:
        base_path = "/app" if os.path.exists("/.dockerenv") else "."
        actual_file_path = os.path.join(base_path, test_file_path)

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(actual_file_path), exist_ok=True)

        with open(actual_file_path, 'w') as f:
            f.write(test_code)

        print(f"\n--- Saved generated test to {test_file_path} ---")
        return True
    except Exception as e:
        print(f"Error saving generated test to file: {e}")
        return False

def run_tests():
    """Runs the JUnit tests and returns the test results."""
    try:
        print("\n--- Running JUnit tests ---")
        if not os.access("./gradlew", os.X_OK):
            os.chmod("./gradlew", 0o755)

        command = ["./gradlew", "test", "--console=plain"]
        print(f"Executing command: {' '.join(command)}")

        process = subprocess.run(command, capture_output=True, text=True, check=False)

        print("Test execution completed.")
        print("\n--- Test Results ---")
        print(process.stdout)

        if process.stderr:
            print("Test errors:")
            print(process.stderr)

        if process.returncode != 0:
            print(f"Warning: Tests finished with non-zero return code: {process.returncode}")
        else:
            print("All tests passed successfully!")

        # Try to find and print the HTML test report
        try:
            base_path = "/app" if os.path.exists("/.dockerenv") else "."
            test_report_path = os.path.join(base_path, "build/reports/tests/test/index.html")

            if os.path.exists(test_report_path):
                print(f"\nDetailed test report is available at: {test_report_path}")
        except Exception:
            pass

        return process.returncode == 0
    except Exception as e:
        print(f"Error running tests: {e}")
        return False

if __name__ == "__main__":
    original_main_java_path = "src/main/java/source/Main.java"
    print(f"\n--- Processing: Original Source File ---")
    original_code_content = get_and_print_code(original_main_java_path, "Original Main.java")
    generated_test_code = None

    if original_code_content:
        generated_test_code = generate_tests_with_llm(original_code_content, "Original Main.java")

    print("\n\n--- Processing: 'bodies' Obfuscation (name changes + body removal) ---")
    if execute_gradle_obfuscation("obfuscated-source-bodies", "bodies"):
        obfuscated_bodies_path = "build/obfuscated-source-bodies/source/Main.java"
        bodies_code_content = get_and_print_code(obfuscated_bodies_path, "Bodies Obfuscated Main.java")
        if bodies_code_content:
            generate_tests_with_llm(bodies_code_content, "Bodies Obfuscated Main.java")
    else:
        print("Obfuscation process for 'bodies' failed. Skipping test generation for this version.")

    print("\n\n--- Processing: 'names' Obfuscation (method and variable name changes) ---")
    if execute_gradle_obfuscation("obfuscated-source-names", "names"):
        obfuscated_names_path = "build/obfuscated-source-names/source/Main.java"
        names_code_content = get_and_print_code(obfuscated_names_path, "Names Obfuscated Main.java")
        if names_code_content:
            generate_tests_with_llm(names_code_content, "Names Obfuscated Main.java")
    else:
        print("Obfuscation process for 'names' failed. Skipping test generation for this version.")

    # Save the generated test from the original code to a file if it was generated
    if generated_test_code:
        test_file_path = "src/test/java/source/LLMGeneratedMainTest.java"
        if save_test_to_file(generated_test_code, test_file_path):
            print("\n\n--- Running JUnit tests with LLM generated tests ---")
            run_tests()
        else:
            print("Failed to save generated tests. Skipping test execution.")
    else:
        print("\nNo test code was generated. Skipping test execution.")

    print("\n\n--- Script Finished ---")
