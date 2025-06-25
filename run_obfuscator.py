import subprocess
import os
import sys
import requests
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
import argparse

# --- Constants for Ollama API ---
OLLAMA_API_URL = "http://rhaegal.dimis.fim.uni-passau.de:15343/api/generate"
OLLAMA_MODEL_NAME = "devstral:24b-small-2505-q8_0"

def clean_test_directory():
    """Deletes all generated test files from the test directory to prevent conflicts."""
    test_dir = "src/test/java/source"
    base_path = "/app" if os.path.exists("/.dockerenv") else "."
    actual_test_dir = os.path.join(base_path, test_dir)

    if not os.path.isdir(actual_test_dir):
        os.makedirs(actual_test_dir, exist_ok=True)
        print(f"Created test directory: {actual_test_dir}")
        return

    print(f"\n--- Cleaning test directory: {actual_test_dir} ---")
    for filename in os.listdir(actual_test_dir):
        if filename.endswith(".java"):
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

def extract_public_methods(java_code_string):
    """Extracts public method names from the provided Java code."""
    method_pattern = r'public\s+[^\s]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('
    return re.findall(method_pattern, java_code_string)

def generate_tests_with_llm(java_code_string, code_description, class_name):
    """Sends Java code to the Ollama API and prints the generated JUnit tests."""
    if not java_code_string:
        print(f"No Java code provided for '{code_description}'. Skipping test generation.")
        return None

    print(f"\n--- Requesting JUnit tests from LLM for: {code_description} ---")
    print(f"(Using model: {OLLAMA_MODEL_NAME} at {OLLAMA_API_URL}))")
    print("Please ensure you are connected to the university VPN.")

    # Generate a specific test class name based on the obfuscation type
    test_class_name = f"LLMGenerated{class_name}Test"
    if "bodies" in code_description.lower():
        test_class_name = f"LLMGenerated{class_name}BodiesTest"
    elif "names" in code_description.lower():
        test_class_name = f"LLMGenerated{class_name}NamesTest"

    # Extract all public method names from the Java code to provide to LLM
    method_names = extract_public_methods(java_code_string)
    method_list = "\n".join([f"- {method}" for method in method_names])


    prompt = f'''    
    You are an expert Java developer tasked with creating JUnit 5 tests.
    
    TASK: Write a valid JUnit 5 test class for the provided Java code. The test class MUST be directly compilable without any modifications.
    
    CONTEXT:
    - The class being tested is: {class_name} 
    - Your test class name MUST be: {test_class_name}
    - The code is in package: source
    
    REQUIREMENTS:
    1. ONLY output valid Java code (no markdown, no explanations, no comments about what you're doing)
    2. Include package declaration: "package source;"
    3. Include these imports:
       import org.junit.jupiter.api.*;
       import static org.junit.jupiter.api.Assertions.*;
       import source.{class_name};
    
    4. If the class has inner classes, also import them explicitly using the proper syntax:
       import source.{class_name}.InnerClassName;
    
    5. ONLY test methods that exist in the provided code. Here are the available public methods:
{method_list}
    
    6. For each method in the class, create AT LEAST 2 test methods:
       - One positive test with valid input demonstrating expected behavior
       - One negative test with invalid input or edge cases
       - Additional test cases for complex methods with multiple code paths
       - Use proper assertions for each test
       - Handle exceptions correctly with try-catch or assertThrows
       - Do NOT access private fields
       - Do NOT create instances of private inner classes directly
       - Do NOT call methods that don't exist in the class
       - Name your test methods clearly (e.g., testMethodName_validInput, testMethodName_invalidInput)
       
    7. IMPORTANT: CAREFULLY CHECK ACCESS MODIFIERS before attempting to use any class members:
       - Do NOT access any private fields (this is not allowed in Java)
       - Do NOT call any private constructors (if the constructor is private, you cannot instantiate directly)
       - Do NOT access protected methods
       - Do NOT access package-private methods
       - ONLY use public methods and constructors
       - Before using ANY member, check its modifier (public, private, protected, package-private)
       - If you see the keyword "private" in the code, that means you CANNOT access that member directly
    
    8. IMPORTANT: For inner classes:
       - NEVER use syntax like 'objectInstance.new InnerClassName()' - this is invalid Java
       - If you need to test code that involves inner classes, only use public methods that return instances of those inner classes
       - Inner class instances must be obtained through public methods that return them
       - If no method returns an inner class instance, then the inner class isn't meant to be directly tested
       - Use proper static nested class syntax if applicable: ClassName.StaticNestedClass
       - NEVER try to instantiate an inner class directly if its constructor has private access
    
    9. IMPORTANT: Do NOT include any explanatory text or markdown - only output valid Java code
    10. IMPORTANT: Your response MUST start with "package source;" and be directly compilable
    
    The Java code to test is as follows:
{java_code_string}
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
    package_pos = code_text.find("package ")
    if package_pos != -1:
        # If "package " is found, strip everything before it
        code_text = code_text[package_pos:]

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
        class_name_to_import = expected_class_name.replace("LLMGenerated", "").replace("Test", "").replace("Bodies", "").replace("Names", "")

        # Replace class declaration to match the file name
        # This ensures the class is named properly regardless of what the LLM generated
        class_pattern = r'(public\s+)?class\s+([A-Za-z0-9_]+)'
        test_code = re.sub(class_pattern, f'class {expected_class_name}', test_code)

        # Ensure source.Main is imported
        if f'import source.{class_name_to_import};' not in test_code:
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
            lines.insert(import_position, f'import source.{class_name_to_import};')
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

        # Print the content of the deobfuscated test file
        base_path = "/app" if os.path.exists("/.dockerenv") else "."
        actual_file_path = os.path.join(base_path, test_file_path)
        try:
            with open(actual_file_path, 'r') as f:
                deobfuscated_content = f.read()
                print(f"\n--- Deobfuscated Test File Content ---")
                print(deobfuscated_content)
                print(f"--- End of Deobfuscated Test File Content ---\n")
        except Exception as e:
            print(f"Warning: Could not read deobfuscated test file: {e}")

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error during deobfuscation: {e}")
        sys.stdout.write("stdout:\n" + e.stdout + "\n")
        sys.stderr.write("stderr:\n" + e.stderr + "\n")
        return False
    except Exception as e:
        print(f"An unexpected error occurred during deobfuscation: {e}")
        return False

def print_test_comparison_table(original_results, bodies_results, names_results):
    """Print a table comparing all test results side by side."""

    if not original_results and not bodies_results and not names_results:
        print("No test results available for comparison.")
        return

    print("\n")
    print("=" * 120)
    print(f"{'DETAILED TEST COMPARISON TABLE':^120}")
    print("=" * 120)

    # Define table headers
    headers = ["Metric", "Original", "Bodies Obfuscated", "Names Obfuscated"]

    # Calculate column widths
    col_width = 30
    header_format = f"{{:<{col_width}}}{{:<{col_width}}}{{:<{col_width}}}{{:<{col_width}}}"

    # Print table headers
    print(header_format.format(*headers))
    print("-" * 120)

    # Basic metrics to compare
    metrics = [
        "Total Tests",
        "Passed Tests",
        "Failed Tests",
        "Skipped Tests",
        "Pass Rate (%)",
        "Total Execution Time (s)"
    ]

    # Print metrics row by row
    for metric in metrics:
        original_value = get_metric_value(original_results, metric)
        bodies_value = get_metric_value(bodies_results, metric)
        names_value = get_metric_value(names_results, metric)

        print(header_format.format(
            metric,
            format_metric_value(original_value, metric),
            format_metric_value(bodies_value, metric),
            format_metric_value(names_value, metric)
        ))

    print("-" * 120)

    # Test coverage comparison - only if all results are available
    if original_results and bodies_results and names_results:
        # Get test methods
        original_methods = set([f"{test['name']}" for test in original_results['tests']])
        bodies_methods = set([f"{test['name']}" for test in bodies_results['tests']])
        names_methods = set([f"{test['name']}" for test in names_results['tests']])

        # All unique test methods
        all_methods = original_methods.union(bodies_methods).union(names_methods)

        # Print test method coverage
        print(f"\n{'Test Method Coverage:':^120}")
        print("-" * 120)
        test_format = f"{{:<{col_width}}}{{:^{col_width}}}{{:^{col_width}}}{{:^{col_width}}}"
        print(test_format.format("Test Method", "Original", "Bodies Obfuscated", "Names Obfuscated"))
        print("-" * 120)

        for method in sorted(all_methods):
            in_original = "✓" if method in original_methods else "✗"
            in_bodies = "✓" if method in bodies_methods else "✗"
            in_names = "✓" if method in names_methods else "✗"

            print(test_format.format(method, in_original, in_bodies, in_names))

    print("=" * 120)

    # Additional analysis on which version performed better
    print(f"\n{'SUMMARY ANALYSIS':^120}")
    print("-" * 120)

    if original_results and bodies_results:
        bodies_pass_rate = bodies_results['passed'] / bodies_results['total'] * 100 if bodies_results['total'] > 0 else 0
        original_pass_rate = original_results['passed'] / original_results['total'] * 100 if original_results['total'] > 0 else 0

        if bodies_pass_rate > original_pass_rate:
            print(f"* Bodies-obfuscated version has a higher pass rate ({bodies_pass_rate:.1f}%) than original ({original_pass_rate:.1f}%)")
        elif bodies_pass_rate < original_pass_rate:
            print(f"* Original version has a higher pass rate ({original_pass_rate:.1f}%) than bodies-obfuscated ({bodies_pass_rate:.1f}%)")
        else:
            print(f"* Original and bodies-obfuscated versions have the same pass rate ({original_pass_rate:.1f}%)")

    if original_results and names_results:
        names_pass_rate = names_results['passed'] / names_results['total'] * 100 if names_results['total'] > 0 else 0
        original_pass_rate = original_results['passed'] / original_results['total'] * 100 if original_results['total'] > 0 else 0

        if names_pass_rate > original_pass_rate:
            print(f"* Names-obfuscated version has a higher pass rate ({names_pass_rate:.1f}%) than original ({original_pass_rate:.1f}%)")
        elif names_pass_rate < original_pass_rate:
            print(f"* Original version has a higher pass rate ({original_pass_rate:.1f}%) than names-obfuscated ({names_pass_rate:.1f}%)")
        else:
            print(f"* Original and names-obfuscated versions have the same pass rate ({original_pass_rate:.1f}%)")

    if bodies_results and names_results:
        bodies_pass_rate = bodies_results['passed'] / bodies_results['total'] * 100 if bodies_results['total'] > 0 else 0
        names_pass_rate = names_results['passed'] / names_results['total'] * 100 if names_results['total'] > 0 else 0

        if bodies_pass_rate > names_pass_rate:
            print(f"* Bodies-obfuscated version has a higher pass rate ({bodies_pass_rate:.1f}%) than names-obfuscated ({names_pass_rate:.1f}%)")
        elif bodies_pass_rate < names_pass_rate:
            print(f"* Names-obfuscated version has a higher pass rate ({names_pass_rate:.1f}%) than bodies-obfuscated ({bodies_pass_rate:.1f}%)")
        else:
            print(f"* Bodies and names-obfuscated versions have the same pass rate ({bodies_pass_rate:.1f}%)")

    print("=" * 120)

def get_metric_value(results, metric):
    """Extract the metric value from test results."""
    if not results:
        return None

    if metric == "Total Tests":
        return results['total']
    elif metric == "Passed Tests":
        return results['passed']
    elif metric == "Failed Tests":
        return results['failed']
    elif metric == "Skipped Tests":
        return results['skipped']
    elif metric == "Pass Rate (%)":
        return results['passed'] / results['total'] * 100 if results['total'] > 0 else 0
    elif metric == "Total Execution Time (s)":
        return results['total_time']
    return None

def format_metric_value(value, metric):
    """Format the metric value for display."""
    if value is None:
        return "N/A"

    if metric in ["Pass Rate (%)", "Total Execution Time (s)"]:
        return f"{value:.2f}"
    else:
        return str(value)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Obfuscate a Java class and generate/run tests.")
    parser.add_argument('--class_name', type=str, default='Main', help='The name of the class to process (e.g., Main, StopWatch).')
    args = parser.parse_args()
    class_name = args.class_name

    # Clean the build directory once at the beginning
    print("\n--- Performing initial clean of the build directory ---")
    subprocess.run(["./gradlew", "clean", "--console=plain"], capture_output=True, text=True)

    original_java_path = f"src/main/java/source/{class_name}.java"
    print(f"\n--- Processing: Original Source File ---")
    original_code_content = get_and_print_code(original_java_path, f"Original {class_name}.java")
    generated_test_code = None
    bodies_test_code = None
    names_code_content = None
    names_test_code = None

    if original_code_content:
        generated_test_code = generate_tests_with_llm(original_code_content, f"Original {class_name}.java", class_name)

    print(f"\n\n--- Processing: 'bodies' Obfuscation (name changes + body removal) ---")
    if execute_gradle_obfuscation("obfuscated-source-bodies", "bodies"):
        obfuscated_bodies_path = f"build/obfuscated-source-bodies/source/{class_name}.java"
        bodies_code_content = get_and_print_code(obfuscated_bodies_path, f"Bodies Obfuscated {class_name}.java")
        if bodies_code_content:
            bodies_test_code = generate_tests_with_llm(bodies_code_content, f"Bodies Obfuscated {class_name}.java", class_name)
    else:
        print("Obfuscation process for 'bodies' failed. Skipping test generation for this version.")

    print(f"\n\n--- Processing: 'names' Obfuscation (method and variable name changes) ---")
    if execute_gradle_obfuscation("obfuscated-source-names", "names"):
        obfuscated_names_path = f"build/obfuscated-source-names/source/{class_name}.java"
        names_code_content = get_and_print_code(obfuscated_names_path, f"Names Obfuscated {class_name}.java")
        if names_code_content:
            names_test_code = generate_tests_with_llm(names_code_content, f"Names Obfuscated {class_name}.java", class_name)
    else:
        print("Obfuscation process for 'names' failed. Skipping test generation for this version.")

    # Save test results
    original_test_results = None
    bodies_test_results = None
    names_test_results = None

    # Save the generated test from the original code to a file if it was generated
    clean_test_directory()
    if generated_test_code:
        test_file_path = f"src/test/java/source/LLMGenerated{class_name}Test.java"
        if save_test_to_file(generated_test_code, test_file_path):
            print(f"\n\n--- Running JUnit tests with LLM generated tests for original code ---")
            success, original_test_results = run_tests()
        else:
            print("Failed to save generated tests. Skipping test execution.")
    else:
        print(f"\nNo test code was generated for original code. Skipping test execution.")

    # Save the generated test from the bodies-obfuscated code to a file if it was generated
    clean_test_directory()
    if bodies_test_code:
        test_file_path = f"src/test/java/source/LLMGenerated{class_name}BodiesTest.java"
        if save_test_to_file(bodies_test_code, test_file_path):
            print(f"\n\n--- Running JUnit tests with LLM generated tests for bodies-obfuscated code ---")
            success, bodies_test_results = run_tests()
        else:
            print("Failed to save generated tests for bodies-obfuscated code. Skipping test execution.")
    else:
        print(f"\nNo test code was generated for bodies-obfuscated code. Skipping test execution.")

    # Save the generated test from the names-obfuscated code to a file if it was generated
    clean_test_directory()
    if names_test_code:
        names_test_file_path = f"src/test/java/source/LLMGenerated{class_name}NamesTest.java"
        if save_test_to_file(names_test_code, names_test_file_path):
            if deobfuscate_tests(names_test_file_path):
                print(f"\n\n--- Running JUnit tests with deobfuscated LLM tests for names-obfuscated code ---")
                success, names_test_results = run_tests()
            else:
                print("Failed to deobfuscate names tests. Skipping test execution.")
        else:
            print("Failed to save generated tests for names-obfuscated code. Skipping test execution.")
    else:
        print(f"\nNo test code was generated for names-obfuscated code. Skipping test execution.")

    # Compare test results if both are available
    if original_test_results and bodies_test_results:
        compare_test_results(original_test_results, bodies_test_results, "Bodies Obfuscated")

    if original_test_results and names_test_results:
        compare_test_results(original_test_results, names_test_results, "Names Obfuscated")

    # Print comprehensive table comparing all three test results
    print_test_comparison_table(original_test_results, bodies_test_results, names_test_results)

