import subprocess
import os
import sys
import requests
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime

# --- Constants for Ollama API ---
OLLAMA_API_URL = "http://rhaegal.dimis.fim.uni-passau.de:15343/api/generate"
OLLAMA_MODEL_NAME = "codellama:7b"

def clean_test_directory():
    """Deletes all generated test files from the test directory to prevent conflicts."""
    test_dir = "src/test/java/source"
    base_path = "/app" if os.path.exists("/.dockerenv") else "."
    actual_test_dir = os.path.join(base_path, test_dir)

    if not os.path.isdir(actual_test_dir):
        return

    print(f"\n--- Cleaning test directory: {actual_test_dir} ---")
    for filename in os.listdir(actual_test_dir):
        if filename.startswith("LLMGenerated") and filename.endswith(".java"):
            try:
                os.remove(os.path.join(actual_test_dir, filename))
                print(f"Removed old test file: {filename}")
            except OSError as e:
                print(f"Error removing file {filename}: {e}")

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

    # Generate a specific test class name based on the obfuscation type
    test_class_name = "LLMGeneratedMainTest"
    if "bodies" in code_description.lower():
        test_class_name = "LLMGeneratedBodiesTest"
    elif "names" in code_description.lower():
        test_class_name = "LLMGeneratedNamesTest"

    prompt = f'''You are an expert Java software developer specializing in writing comprehensive unit tests.
        Your task is to generate a complete JUnit 5 test class for the provided Java code.
        Instructions:
        1. The test class must be fully self-contained and ready to compile.
        2. IMPORTANT: Include all necessary JUnit 5 imports: `import org.junit.jupiter.api.*;`, `import static org.junit.jupiter.api.Assertions.*;`, and `import source.Main;`.
        3. For each public method in the provided code, generate EXACTLY 2 test methods:
           a. A "positive" test case: This test should verify the method\'s functionality with valid, typical inputs where no errors or exceptions are expected. Use assertions like `assertEquals` or `assertTrue` to validate the outcome.
           b. A "negative" or "edge case" test: This test should verify the method\'s behavior with invalid inputs or edge cases.
              - **If the method can throw exceptions** (declared, documented, or clearly inferable like `NullPointerException` or division-by-zero `ArithmeticException`): Use `assertThrows` to test these exception scenarios. Do not invent unlikely exceptions. If multiple exceptions are possible, test them all in this one test method.
              - **If the method does not throw exceptions**: Test it with edge-case inputs. Examples include `null`, empty arrays, zero, negative numbers, or boundary values like `Integer.MAX_VALUE`. The goal is to check for unexpected behavior or incorrect results.
        4. Generate tests only for public methods explicitly defined in the provided code.
        5. Use appropriate assertions (`assertEquals`, `assertTrue`, etc.) for methods with return values. For void methods, test for side effects or ensure they run without errors for valid inputs.
        6. IMPORTANT: The test class MUST be named "{test_class_name}".
        7. Handle object instantiation correctly (e.g., `Main main = new Main();`) for instance methods and call static methods directly on the class (e.g., `Main.methodName();`).
        8. IMPORTANT: Provide only the raw Java code for the test class. Do not include markdown fences (```java) or any explanatory text.

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

        # Ensure proper imports are present
        cleaned_code = ensure_junit_imports(cleaned_code)

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

def ensure_junit_imports(code_text):
    """Ensure that necessary JUnit imports are present in the code."""
    # Check if static imports for assertions are present
    static_assertion_import = "import static org.junit.jupiter.api.Assertions.*;"
    junit_api_import = "import org.junit.jupiter.api.*;"
    arrays_import = "import java.util.Arrays;"

    # Check if code already has the imports
    has_static_assertions = "import static org.junit.jupiter.api.Assertions" in code_text
    has_junit_api = "import org.junit.jupiter.api" in code_text
    needs_arrays = 'assertArrayEquals' in code_text or 'Arrays.toString' in code_text or 'Arrays.equals' in code_text
    has_arrays = arrays_import in code_text

    # Find package statement or the first line to insert imports after
    lines = code_text.splitlines()
    insert_position = 0

    for i, line in enumerate(lines):
        if line.strip().startswith("package "):
            insert_position = i + 1
            break

    # Insert missing imports
    if not has_static_assertions:
        lines.insert(insert_position, static_assertion_import)
        insert_position += 1

    if not has_junit_api:
        lines.insert(insert_position, junit_api_import)
        insert_position += 1

    if needs_arrays and not has_arrays:
        lines.insert(insert_position, arrays_import)
        insert_position += 1

    # Add an empty line after imports if there isn't one already
    if insert_position < len(lines) and lines[insert_position].strip() != "":
        lines.insert(insert_position, "")

    return "\n".join(lines)

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

        # Extract the expected class name from the file path
        expected_class_name = os.path.splitext(os.path.basename(test_file_path))[0]

        # Replace class declaration to match the file name
        # This ensures the class is named properly regardless of what the LLM generated
        class_pattern = r'(public\s+)?class\s+([A-Za-z0-9_]+)'
        test_code = re.sub(class_pattern, f'class {expected_class_name}', test_code)

        # Ensure source.Main is imported
        if 'import source.Main;' not in test_code:
            # Find where to insert the import
            import_position = 0
            lines = test_code.splitlines()
            for i, line in enumerate(lines):
                if line.strip().startswith('import '):
                    import_position = i + 1
                elif line.strip().startswith('class ') and import_position == 0:
                    import_position = i
                    break

            # Insert the import
            lines.insert(import_position, 'import source.Main;')
            test_code = '\n'.join(lines)

        with open(actual_file_path, 'w') as f:
            f.write(test_code)

        print(f"\n--- Saved generated test to {test_file_path} ---")
        return True
    except Exception as e:
        print(f"Error saving generated test to file: {e}")
        return False

def parse_test_results():
    """Parse the JUnit XML test results to provide detailed test information."""
    base_path = "/app" if os.path.exists("/.dockerenv") else "."
    test_results_dir = os.path.join(base_path, "build/test-results/test")

    if not os.path.exists(test_results_dir):
        print("No test results directory found.")
        return None

    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "tests": [],
        "total_time": 0
    }

    # Find all XML files in test results directory
    xml_files = [f for f in os.listdir(test_results_dir) if f.endswith(".xml")]

    for xml_file in xml_files:
        try:
            tree = ET.parse(os.path.join(test_results_dir, xml_file))
            testsuite = tree.getroot()

            # Get test suite information
            results["total"] += int(testsuite.get("tests", 0))
            results["failed"] += int(testsuite.get("failures", 0)) + int(testsuite.get("errors", 0))
            results["skipped"] += int(testsuite.get("skipped", 0))

            suite_time = float(testsuite.get("time", 0))
            results["total_time"] += suite_time

            suite_name = testsuite.get("name", "Unknown")

            # Process individual test cases
            for testcase in testsuite.findall(".//testcase"):
                test_info = {
                    "suite": suite_name,
                    "name": testcase.get("name", "Unknown"),
                    "class": testcase.get("classname", "Unknown"),
                    "time": float(testcase.get("time", 0)),
                    "status": "PASSED"
                }

                # Check for failures or errors
                if testcase.find("failure") is not None or testcase.find("error") is not None:
                    test_info["status"] = "FAILED"

                    if testcase.find("failure") is not None:
                        failure = testcase.find("failure")
                        test_info["failure_type"] = failure.get("type", "Unknown")
                        test_info["failure_message"] = failure.get("message", "No message")

                    if testcase.find("error") is not None:
                        error = testcase.find("error")
                        test_info["error_type"] = error.get("type", "Unknown")
                        test_info["error_message"] = error.get("message", "No message")

                # Check for skipped tests
                if testcase.find("skipped") is not None:
                    test_info["status"] = "SKIPPED"

                results["tests"].append(test_info)

        except Exception as e:
            print(f"Error parsing test results file {xml_file}: {e}")

    results["passed"] = results["total"] - results["failed"] - results["skipped"]
    return results

def print_detailed_test_report(results):
    """Prints a detailed, formatted report of test results."""
    if not results:
        print("No test results available.")
        return

    print("\n")
    print("=" * 80)
    print(f"{'TEST EXECUTION SUMMARY':^80}")
    print("=" * 80)
    print(f"Total Tests: {results['total']}")
    print(f"Tests Passed: {results['passed']} ({results['passed']/results['total']*100:.1f}%)")
    print(f"Tests Failed: {results['failed']} ({results['failed']/results['total']*100:.1f}%)")
    print(f"Tests Skipped: {results['skipped']} ({results['skipped']/results['total']*100:.1f}%)")
    print(f"Total Execution Time: {results['total_time']:.3f} seconds")
    print("=" * 80)

    # Print test details in a table
    print(f"{'STATUS':<10} {'TEST CLASS':<30} {'TEST METHOD':<30} {'TIME (s)':<10}")
    print("-" * 80)

    # Sort tests by status (failures first) and then by execution time (slowest first)
    sorted_tests = sorted(results['tests'], key=lambda x: (0 if x['status'] == 'FAILED' else (1 if x['status'] == 'SKIPPED' else 2), -x['time']))

    for test in sorted_tests:
        status_color = ""
        status_end = ""

        # If in a terminal environment, add colors
        if sys.stdout.isatty():
            if test['status'] == 'PASSED':
                status_color = "\033[92m"  # Green
            elif test['status'] == 'FAILED':
                status_color = "\033[91m"  # Red
            elif test['status'] == 'SKIPPED':
                status_color = "\033[93m"  # Yellow
            status_end = "\033[0m"  # Reset color

        class_name = test['class'].split('.')[-1]  # Just the class name without package
        print(f"{status_color}{test['status']:<10}{status_end} {class_name:<30} {test['name']:<30} {test['time']:.3f}")

        # Print failure details if test failed
        if test['status'] == 'FAILED' and ('failure_message' in test or 'error_message' in test):
            print(f"    Failure: {test.get('failure_message', test.get('error_message', 'Unknown error'))}")

    print("=" * 80)

    # Print HTML report location
    base_path = "/app" if os.path.exists("/.dockerenv") else "."
    test_report_path = os.path.join(base_path, "build/reports/tests/test/index.html")
    if os.path.exists(test_report_path):
        print(f"Detailed HTML report: {test_report_path}")

    print("=" * 80)

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
        print("\n--- Test Results (Gradle Output) ---")
        print(process.stdout)

        if process.stderr:
            print("Test errors:")
            print(process.stderr)

        # Parse and print detailed test results
        print("\n--- Detailed Test Results ---")
        test_results = parse_test_results()
        if test_results:
            print_detailed_test_report(test_results)
        else:
            print("No detailed test results available.")

        if process.returncode != 0:
            print(f"Warning: Tests finished with non-zero return code: {process.returncode}")
        else:
            print("All tests passed successfully!")

        return process.returncode == 0, test_results
    except Exception as e:
        print(f"Error running tests: {e}")
        return False, None

def compare_test_results(original_results, other_results, other_name):
    """Compare test results between original and another set of tests."""
    if not original_results or not other_results:
        print("Cannot compare test results - one or both result sets are missing.")
        return

    print("\n")
    print("=" * 80)
    print(f"{f'COMPARISON: ORIGINAL VS {other_name.upper()} TESTS':^80}")
    print("=" * 80)

    print(f"{'Metric':<30} {'Original':<20} {other_name:<20} {'Difference':<10}")
    print("-" * 80)

    # Compare basic metrics
    metrics = [
        ("Total Tests", original_results['total'], other_results['total']),
        ("Passed Tests", original_results['passed'], other_results['passed']),
        ("Failed Tests", original_results['failed'], other_results['failed']),
        ("Skipped Tests", original_results['skipped'], other_results['skipped']),
        ("Pass Rate (%)", original_results['passed']/original_results['total']*100 if original_results['total'] > 0 else 0,
                           other_results['passed']/other_results['total']*100 if other_results['total'] > 0 else 0),
        ("Total Execution Time (s)", original_results['total_time'], other_results['total_time'])
    ]

    for metric_name, original_value, other_value in metrics:
        if isinstance(original_value, int):
            diff = other_value - original_value
            print(f"{metric_name:<30} {original_value:<20d} {other_value:<20d} {diff:+d}")
        else:
            diff = other_value - original_value
            print(f"{metric_name:<30} {original_value:<20.3f} {other_value:<20.3f} {diff:+.3f}")

    print("=" * 80)

    # Compare test methods between the two result sets
    original_test_methods = {f"{test['class']}::{test['name']}": test for test in original_results['tests']}
    other_test_methods = {f"{test['class']}::{test['name']}": test for test in other_results['tests']}

    # Find unique tests in each set
    original_unique = set(original_test_methods.keys()) - set(other_test_methods.keys())
    other_unique = set(other_test_methods.keys()) - set(original_test_methods.keys())
    common_tests = set(original_test_methods.keys()) & set(other_test_methods.keys())

    # Print unique tests
    if original_unique:
        print("\nTests only in Original:")
        for test_key in sorted(original_unique):
            test = original_test_methods[test_key]
            print(f"  - {test['class'].split('.')[-1]}::{test['name']} ({test['status']})")

    if other_unique:
        print(f"\nTests only in {other_name}:")
        for test_key in sorted(other_unique):
            test = other_test_methods[test_key]
            print(f"  - {test['class'].split('.')[-1]}::{test['name']} ({test['status']})")

    # Compare status of common tests
    status_changes = []
    for test_key in common_tests:
        original_status = original_test_methods[test_key]['status']
        other_status = other_test_methods[test_key]['status']

        if original_status != other_status:
            status_changes.append((test_key, original_status, other_status))

    if status_changes:
        print("\nTests with changed status:")
        for test_key, original_status, other_status in sorted(status_changes):
            test_name = test_key.split('::')[1]
            class_name = test_key.split('::')[0].split('.')[-1]
            print(f"  - {class_name}::{test_name}: {original_status} → {other_status}")

    print("=" * 80)

def deobfuscate_tests(test_file_path):
    """Deobfuscates a test file by replacing obfuscated method names with original names."""
    try:
        print(f"\n--- Deobfuscating test file: {test_file_path} ---")
        if not os.access("./gradlew", os.X_OK):
            os.chmod("./gradlew", 0o755)

        # Run the deobfuscator using the 'deobfuscate' task.
        # The deobfuscator now modifies the file in-place.
        command = ["./gradlew", "deobfuscate", f"--args={test_file_path}", "--console=plain"]

        print(f"Executing command: {' '.join(command)}")
        process = subprocess.run(command, capture_output=True, text=True, check=False)

        print(f"Deobfuscation process completed.")
        sys.stdout.write("stdout:\n" + process.stdout + "\n")
        if process.stderr:
            sys.stderr.write("stderr:\n" + process.stderr + "\n")

        if process.returncode != 0:
            print(f"Error: Deobfuscation process failed with return code {process.returncode}.")
            return False

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error during deobfuscation: {e}")
        sys.stdout.write("stdout:\n" + e.stdout + "\n")
        sys.stderr.write("stderr:\n" + e.stderr + "\n")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during deobfuscation: {e}")
        return False

if __name__ == "__main__":
    original_main_java_path = "src/main/java/source/Main.java"
    print(f"\n--- Processing: Original Source File ---")
    original_code_content = get_and_print_code(original_main_java_path, "Original Main.java")
    generated_test_code = None
    bodies_test_code = None
    names_code_content = None

    if original_code_content:
        generated_test_code = generate_tests_with_llm(original_code_content, "Original Main.java")

    print("\n\n--- Processing: 'bodies' Obfuscation (name changes + body removal) ---")
    if execute_gradle_obfuscation("obfuscated-source-bodies", "bodies"):
        obfuscated_bodies_path = "build/obfuscated-source-bodies/source/Main.java"
        bodies_code_content = get_and_print_code(obfuscated_bodies_path, "Bodies Obfuscated Main.java")
        if bodies_code_content:
            bodies_test_code = generate_tests_with_llm(bodies_code_content, "Bodies Obfuscated Main.java")
    else:
        print("Obfuscation process for 'bodies' failed. Skipping test generation for this version.")

    print("\n\n--- Processing: 'names' Obfuscation (method and variable name changes) ---")
    if execute_gradle_obfuscation("obfuscated-source-names", "names"):
        obfuscated_names_path = "build/obfuscated-source-names/source/Main.java"
        names_code_content = get_and_print_code(obfuscated_names_path, "Names Obfuscated Main.java")
        if names_code_content:
            names_test_code = generate_tests_with_llm(names_code_content, "Names Obfuscated Main.java")
    else:
        print("Obfuscation process for 'names' failed. Skipping test generation for this version.")

    # Save test results
    original_test_results = None
    bodies_test_results = None
    names_test_results = None

    # Save the generated test from the original code to a file if it was generated
    clean_test_directory()
    if generated_test_code:
        test_file_path = "src/test/java/source/LLMGeneratedMainTest.java"
        if save_test_to_file(generated_test_code, test_file_path):
            print("\n\n--- Running JUnit tests with LLM generated tests for original code ---")
            success, original_test_results = run_tests()
        else:
            print("Failed to save generated tests. Skipping test execution.")
    else:
        print("\nNo test code was generated for original code. Skipping test execution.")

    # Save the generated test from the bodies-obfuscated code to a file if it was generated
    clean_test_directory()
    if bodies_test_code:
        test_file_path = "src/test/java/source/LLMGeneratedBodiesTest.java"
        if save_test_to_file(bodies_test_code, test_file_path):
            print("\n\n--- Running JUnit tests with LLM generated tests for bodies-obfuscated code ---")
            success, bodies_test_results = run_tests()
        else:
            print("Failed to save generated tests for bodies-obfuscated code. Skipping test execution.")
    else:
        print("\nNo test code was generated for bodies-obfuscated code. Skipping test execution.")

    # Save the generated test from the names-obfuscated code to a file if it was generated
    clean_test_directory()
    if names_test_code:
        names_test_file_path = "src/test/java/source/LLMGeneratedNamesTest.java"
        if save_test_to_file(names_test_code, names_test_file_path):
            if deobfuscate_tests(names_test_file_path):
                print(f"\n\n--- Running JUnit tests with deobfuscated LLM tests for names-obfuscated code ---")
                success, names_test_results = run_tests()
            else:
                print("Failed to deobfuscate names tests. Skipping test execution.")
        else:
            print("Failed to save generated tests for names-obfuscated code. Skipping test execution.")
    else:
        print("\nNo test code was generated for names-obfuscated code. Skipping test execution.")

    # Compare test results if both are available
    if original_test_results and bodies_test_results:
        compare_test_results(original_test_results, bodies_test_results, "Bodies-Obfuscated")

    if original_test_results and names_test_results:
        compare_test_results(original_test_results, names_test_results, "Names-Obfuscated (Deobfuscated)")

    print("\n\n--- Script Finished ---")
