# Java Code Obfuscation Demo for LLM-based Test Generation Analysis

This project is part of a seminar work investigating the effects of code obfuscation on LLM-based test generation. It provides a configurable Java code obfuscator using the Spoon library, a deobfuscator for test files, and a Dockerized environment to run the complete obfuscation and test generation pipeline.

## Project Overview

The primary goal is to apply different obfuscation techniques to Java classes from a pet clinic domain and then analyze how these changes impact the ability of Large Language Models (LLMs) to generate meaningful unit tests.

### Key Components

1. **Obfuscator** (`com.obfuscationdemo.Obfuscator`): Applies obfuscation techniques using Spoon
2. **Deobfuscator** (`com.obfuscationdemo.Deobfuscator`): Reverses name obfuscation in test files using stored mappings
3. **Test Generator**: Uses LLMs (DevStral) to generate JUnit 5 tests for obfuscated code
4. **Analysis Pipeline**: Compares test generation effectiveness across different obfuscation levels

### Obfuscation Techniques

The obfuscator currently supports:
- **Name Obfuscation**: Renames methods, parameters, local variables, and fields, strips all comments including JavaDoc
- **Body Removal**: Removes method bodies, replacing them with default return values

### Sample Classes

The project includes a comprehensive set of Java classes from a pet clinic domain:

**Core Service Classes:**
- `ClinicService.java` - Service interface
- `ClinicServiceImpl.java` - Service implementation with Spring annotations

**Entity Classes:**
- `Owner.java` - Pet owner entity
- `Pet.java` - Pet entity  
- `Vet.java` - Veterinarian entity
- `Visit.java` - Clinic visit entity
- `PetType.java` - Pet type/breed entity
- `Specialty.java` - Veterinary specialty entity

**Repository Interfaces:**
- `OwnerRepository.java`
- `PetRepository.java`
- `VetRepository.java`
- `VisitRepository.java`
- `PetTypeRepository.java`
- `SpecialtyRepository.java`

**Utility Classes:**
- `Main.java` - Simple demonstration class
- `StopWatch.java` - Timing utility

## Obfuscation Modes

The Python script `run_obfuscator.py` orchestrates the process with three modes:

1. **`original`**: Uses unmodified source code for baseline test generation
2. **`bodies`**: Removes method bodies only (preserves method signatures)
3. **`names`**: Applies comprehensive name obfuscation (methods, parameters, variables, fields)

Output directories:
- Original tests: Generated from `src/main/java/source/`
- Bodies mode: `build/obfuscated-source-bodies/`
- Names mode: `build/obfuscated-source-names/` (with deobfuscation applied to tests)

## Getting Started with Docker

### Prerequisites
- Docker installed and running
- Access to University of Passau VPN (for LLM API access)

### Basic Usage

1. **Build the Docker image**:
   ```bash
   docker build -t obfuscator-app .
   ```

2. **Run with specific class**:
   ```bash
   docker run --rm obfuscator-app --class_name Clinic
