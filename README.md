# Java Code Obfuscation Demo for LLM-based Test Generation Analysis

This project is part of a seminar work investigating the effects of code obfuscation on LLM-based test generation. It provides a configurable Java code obfuscator using the Spoon library and a Dockerized environment to run the obfuscation process.

## Project Overview

The primary goal is to apply different obfuscation techniques to a sample Java codebase and then analyze how these changes impact the ability of Large Language Models (LLMs) to generate meaningful unit tests.

The obfuscator currently supports:
- **Name Obfuscation**: Renames methods, parameters, and local variables.
- **Body Removal**: Removes method bodies, replacing them with default return values.

The Python script `run_obfuscator.py` orchestrates the obfuscation process by invoking a Gradle task (`spoonObfuscate`). This task uses the `com.obfuscationdemo.Obfuscator` Java class, which leverages Spoon to parse and transform the Java source code.

Two modes of obfuscation are currently demonstrated by the script:
1.  **`bodies` mode**: Removes method bodies. Output is directed to `build/obfuscated-source-bodies/`.
2.  **`names` mode**: Applies only name obfuscation (methods, parameters, local variables). Output is directed to `build/obfuscated-source-names/`.

## Getting Started with Docker

To build and run the obfuscation process within a Docker container, follow these steps:

1.  **Ensure Docker is installed and running** on your system.

2.  **Clone the repository** (if you haven't already):
    ```bash
    # git clone <repository-url>
    cd obfuscation-demo
    ```

3.  **Build the Docker image**:
    Open your terminal in the project root directory (`obfuscation-demo`) and run:
    ```bash
    docker build -t obfuscator-app .
    ```
    This command reads the `Dockerfile`, downloads the necessary base image (Gradle with JDK 17), copies your project files into the image, installs Python, and sets up the environment.

4.  **Run the Docker container**:
    After the image is successfully built, run the following command:
    ```bash
    docker run --rm obfuscator-app
    ```
    This command starts a container from the `obfuscator-app` image. The `--rm` flag ensures the container is automatically removed after it exits.

    The container will execute the `run_obfuscator.py` script. This script performs the following actions:
    *   Invokes the Gradle task `spoonObfuscate` twice, once for each obfuscation mode (`bodies` and `names`).
    *   The Gradle task, in turn, runs the Java obfuscator (`com.obfuscationdemo.Obfuscator`) with the appropriate arguments for each mode.
    *   The Python script then prints the standard output from the Gradle tasks and the content of the obfuscated `Main.java` file for each mode to your terminal.

## Project Structure Highlights

-   `src/main/java/com/obfuscationdemo/Obfuscator.java`: The core Java class responsible for code obfuscation using Spoon.
-   `src/main/java/source/Main.java`: The sample Java file that will be obfuscated.
-   `build.gradle`: Defines project dependencies (Spoon, JUnit) and custom Gradle tasks for obfuscation (`spoonObfuscate`, `compileObfuscatedSource`, `obfuscatedJar`).
-   `run_obfuscator.py`: Python script to automate running the obfuscation tasks and displaying results.
-   `Dockerfile`: Defines the Docker image for running the obfuscation in an isolated environment.
-   `build/obfuscated-source-bodies/`: Output directory for the 'bodies' obfuscation mode.
-   `build/obfuscated-source-names/`: Output directory for the 'names' obfuscation mode.
