package com.obfuscationdemo;

import spoon.Launcher;
import spoon.processing.AbstractProcessor;
import spoon.reflect.code.CtInvocation;
import spoon.reflect.declaration.CtMethod;
import spoon.reflect.reference.CtExecutableReference;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.ObjectInputStream;
import java.nio.file.Paths;
import java.util.HashMap;
import java.util.Map;

/**
 * Deobfuscator class that applies reverse mappings to convert
 * obfuscated method names back to original names in test files.
 */
public class Deobfuscator {
    private static final String MAPPING_FILE = "build/obfuscation-mapping.ser";
    private Map<String, String> reverseMethodMapping = new HashMap<>();

    public static void main(String[] args) {
        if (args.length == 0) {
            System.err.println("Error: No input file specified for deobfuscation.");
            System.exit(1);
        }
        String inputTestFile = args[0];

        System.out.println("Starting deobfuscation process for: " + inputTestFile);

        Deobfuscator deobfuscator = new Deobfuscator();
        if (deobfuscator.loadMappings()) {
            deobfuscator.deobfuscateTestFile(inputTestFile);
        } else {
            System.err.println("Failed to load obfuscation mappings. Deobfuscation cannot proceed.");
            System.exit(1);
        }
    }

    /**
     * Load the obfuscation mappings from the serialized file and create reverse mappings.
     */
    public boolean loadMappings() {
        File file = new File(MAPPING_FILE);
        if (!file.exists()) {
            System.err.println("Mapping file not found: " + file.getAbsolutePath());
            return false;
        }

        try (FileInputStream fis = new FileInputStream(file);
             ObjectInputStream ois = new ObjectInputStream(fis)) {

            Object obj = ois.readObject();
            if (!(obj instanceof Obfuscator.ObfuscationMappings)) {
                System.err.println("Invalid mapping file format");
                return false;
            }

            Obfuscator.ObfuscationMappings mappings = (Obfuscator.ObfuscationMappings) obj;

            // Create reverse method mappings (obfuscated -> original)
            for (Map.Entry<String, String> entry : mappings.getMethodMappings().entrySet()) {
                String originalName = entry.getKey();
                String obfuscatedName = entry.getValue();
                reverseMethodMapping.put(obfuscatedName, originalName);
            }

            System.out.println("Loaded " + reverseMethodMapping.size() + " method name mappings");
            return true;

        } catch (IOException | ClassNotFoundException e) {
            System.err.println("Error loading obfuscation mappings: " + e.getMessage());
            e.printStackTrace();
            return false;
        }
    }

    /**
     * Deobfuscate a test file by replacing obfuscated method names with original names.
     * The modification is done in-place.
     */
    public void deobfuscateTestFile(String inputFile) {
        System.out.println("Processing test file with Spoon (in-place)...");
        try {
            Launcher launcher = new Launcher();
            launcher.addInputResource(inputFile);
            // Tell Spoon to write output back to the source directory's parent to avoid nested source/source
            launcher.setSourceOutputDirectory(Paths.get(inputFile).getParent().getParent().toFile());
            launcher.getEnvironment().setAutoImports(true);

            launcher.addProcessor(new MethodInvocationDeobfuscator(reverseMethodMapping));
            launcher.addProcessor(new TestMethodNameDeobfuscator(reverseMethodMapping));

            launcher.run();
            System.out.println("Deobfuscation completed! The file has been updated: " + inputFile);
        } catch (Exception e) {
            System.err.println("Error during deobfuscation: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }

    /**
     * Processor to replace obfuscated method names with original names in method invocations.
     */
    private static class MethodInvocationDeobfuscator extends AbstractProcessor<CtInvocation<?>> {
        private final Map<String, String> reverseMethodMapping;

        public MethodInvocationDeobfuscator(Map<String, String> reverseMethodMapping) {
            this.reverseMethodMapping = reverseMethodMapping;
        }

        @Override
        public void process(CtInvocation<?> invocation) {
            CtExecutableReference<?> execRef = invocation.getExecutable();
            String methodName = execRef.getSimpleName();

            if (reverseMethodMapping.containsKey(methodName)) {
                String originalName = reverseMethodMapping.get(methodName);
                execRef.setSimpleName(originalName);
                System.out.println("Replaced method invocation: " + methodName + " -> " + originalName);
            }
        }
    }

    /**
     * Processor to replace obfuscated method names in test method names
     */
    private static class TestMethodNameDeobfuscator extends AbstractProcessor<CtMethod<?>> {
        private final Map<String, String> reverseMethodMapping;

        public TestMethodNameDeobfuscator(Map<String, String> reverseMethodMapping) {
            this.reverseMethodMapping = reverseMethodMapping;
        }

        @Override
        public void process(CtMethod<?> method) {
            String methodName = method.getSimpleName();

            // Look for test methods that might be testing obfuscated methods
            for (Map.Entry<String, String> entry : reverseMethodMapping.entrySet()) {
                String obfuscatedName = entry.getKey();
                String originalName = entry.getValue();

                // Check if the test method name contains the obfuscated name
                if (methodName.contains(obfuscatedName)) {
                    String newMethodName = methodName.replace(obfuscatedName, originalName);
                    method.setSimpleName(newMethodName);
                    System.out.println("Renamed test method: " + methodName + " -> " + newMethodName);
                } else if (methodName.equals("test" + obfuscatedName) ||
                         methodName.equals("test" + capitalize(obfuscatedName))) {
                    String newMethodName = "test" + capitalize(originalName);
                    method.setSimpleName(newMethodName);
                    System.out.println("Renamed test method: " + methodName + " -> " + newMethodName);
                }
            }
        }

        private String capitalize(String str) {
            if (str == null || str.isEmpty()) {
                return str;
            }
            return Character.toUpperCase(str.charAt(0)) + str.substring(1);
        }
    }
}
