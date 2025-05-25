#!/usr/bin/env bash
set -euo pipefail

echo "=== Java Code Obfuscation Analysis ==="

# Build and obfuscate the project
echo "Building project..."
./gradlew clean build

echo "Running ProGuard obfuscation..."
./gradlew proguard

# Prepare output directories
mkdir -p decompiled/original
mkdir -p decompiled/obfuscated

# Download CFR decompiler if missing
CFR_JAR="cfr-0.152.jar"
if [[ ! -f "$CFR_JAR" ]]; then
  echo "Downloading CFR Java decompiler..."
  curl -L -o "$CFR_JAR" \
    "https://github.com/leibnitz27/cfr/releases/download/0.152/cfr-0.152.jar"
fi

# Locate original and obfuscated JAR artifacts
VERSION="1.0-SNAPSHOT"
ORIG_JAR=$(ls build/libs/*"${VERSION}".jar | grep -v obfuscated)
OBF_JAR=$(ls build/libs/*-obfuscated.jar)

echo ""
echo "=== ORIGINAL JAVA CODE ==="
java -jar "$CFR_JAR" "$ORIG_JAR" \
     --outputdir decompiled/original/ --caseinsensitivefs true
echo ""
echo "Original decompiled code:"
find decompiled/original -name "*.java" -exec cat {} \;

echo ""
echo "=========================================="
echo ""

echo "=== OBFUSCATED JAVA CODE ==="
java -jar "$CFR_JAR" "$OBF_JAR" \
     --outputdir decompiled/obfuscated/ --caseinsensitivefs true
echo ""
echo "Obfuscated decompiled code:"
find decompiled/obfuscated -name "*.java" -exec cat {} \;

echo ""
echo "=========================================="
echo ""

# Compare file sizes
echo "=== FILE SIZE COMPARISON ==="
echo "Original JAR:"
ls -lh "$ORIG_JAR"
echo "Obfuscated JAR:"
ls -lh "$OBF_JAR"

echo ""
echo "=== OBFUSCATION SUMMARY ==="
echo "Decompiled files saved in:"
echo "  - Original: decompiled/original/"
echo "  - Obfuscated: decompiled/obfuscated/"

# Count decompiled Java source files
orig_classes=$(find decompiled/original -name "*.java" | wc -l)
obf_classes=$(find decompiled/obfuscated -name "*.java" | wc -l)
echo ""
echo "Class count comparison:"
echo "  Original classes:  $orig_classes"
echo "  Obfuscated classes: $obf_classes"

echo ""
echo "=== BYTECODE ANALYSIS ==="
echo "Original main() bytecode:"
javap -c -cp "$ORIG_JAR" com.obfuscationdemo.Main | sed -n '1,20p'

echo ""
echo "Obfuscated main() bytecode:"
javap -c -cp "$OBF_JAR" com.obfuscationdemo.Main | sed -n '1,20p'
