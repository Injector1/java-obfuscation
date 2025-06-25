package com.obfuscationdemo;

import spoon.Launcher;
import spoon.processing.AbstractProcessor;
import spoon.reflect.code.CtInvocation;
import spoon.reflect.code.CtExecutableReferenceExpression;
import spoon.reflect.code.CtFieldAccess;
import spoon.reflect.declaration.CtMethod;
import spoon.reflect.reference.CtExecutableReference;
import spoon.reflect.reference.CtFieldReference;

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
    private Map<String, String> reverseTypeMapping = new HashMap<>();
    private Map<String, Map<String, String>> reverseFieldMapping = new HashMap<>();

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

            // Create reverse type mappings (obfuscated -> original) if available
            try {
                Map<String, String> typeMappings = mappings.getTypeMappings();
                if (typeMappings != null) {
                    for (Map.Entry<String, String> entry : typeMappings.entrySet()) {
                        String originalName = entry.getKey();
                        String obfuscatedName = entry.getValue();
                        reverseTypeMapping.put(obfuscatedName, originalName);
                    }
                    System.out.println("Loaded " + reverseTypeMapping.size() + " type name mappings");
                }
            } catch (Exception e) {
                System.out.println("No type mappings found in obfuscation data");
            }

            // Create reverse field mappings (obfuscated -> original)
            try {
                Map<String, Map<String, String>> fieldMappings = mappings.getFieldMappings();
                if (fieldMappings != null) {
                    for (Map.Entry<String, Map<String, String>> classEntry : fieldMappings.entrySet()) {
                        String className = classEntry.getKey();
                        Map<String, String> fieldMap = classEntry.getValue();

                        // Create reverse mapping for this class
                        Map<String, String> reverseFieldsForClass = new HashMap<>();
                        reverseFieldMapping.put(className, reverseFieldsForClass);

                        // Fill the reverse mapping
                        for (Map.Entry<String, String> fieldEntry : fieldMap.entrySet()) {
                            String originalFieldName = fieldEntry.getKey();
                            String obfuscatedFieldName = fieldEntry.getValue();
                            reverseFieldsForClass.put(obfuscatedFieldName, originalFieldName);
                        }
                    }

                    int totalFields = reverseFieldMapping.values().stream()
                        .mapToInt(map -> map.size())
                        .sum();
                    System.out.println("Loaded " + totalFields + " field name mappings for " +
                                       reverseFieldMapping.size() + " classes");
                }
            } catch (Exception e) {
                System.out.println("No field mappings found in obfuscation data: " + e.getMessage());
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
     * The modification is done in-place using Spoon's AST transformations.
     */
    public void deobfuscateTestFile(String inputFile) {
        System.out.println("Processing test file with Spoon (in-place)...");
        try {
            Launcher launcher = new Launcher();
            launcher.addInputResource(inputFile);
            // Set the output directory to the root of the test source to avoid nested package dirs
            launcher.setSourceOutputDirectory(Paths.get(inputFile).getParent().getParent().toFile());
            
            // Set compilation and environment options
            launcher.getEnvironment().setComplianceLevel(17); // Ensure Java 17 compatibility
            launcher.getEnvironment().setCommentEnabled(true); // Preserve comments
            launcher.getEnvironment().setAutoImports(false);  // Don't modify imports
            launcher.getEnvironment().setNoClasspath(true);   // Avoid classpath issues
            
            // Add all processors for deobfuscation
            launcher.addProcessor(new MethodInvocationDeobfuscator(reverseMethodMapping));
            launcher.addProcessor(new TestMethodNameDeobfuscator(reverseMethodMapping));
            launcher.addProcessor(new MethodReferenceDeobfuscator(reverseMethodMapping));
            launcher.addProcessor(new MethodAccessInBodyDeobfuscator(reverseMethodMapping));
            launcher.addProcessor(new FieldAccessDeobfuscator(reverseFieldMapping));

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

    /**
     * Processor to replace obfuscated method names in method references (:: syntax)
     */
    private static class MethodReferenceDeobfuscator extends AbstractProcessor<CtExecutableReferenceExpression<?, ?>> {
        private final Map<String, String> reverseMethodMapping;

        public MethodReferenceDeobfuscator(Map<String, String> reverseMethodMapping) {
            this.reverseMethodMapping = reverseMethodMapping;
        }

        @Override
        public void process(CtExecutableReferenceExpression<?, ?> reference) {
            CtExecutableReference<?> execRef = reference.getExecutable();
            String methodName = execRef.getSimpleName();

            if (reverseMethodMapping.containsKey(methodName)) {
                String originalName = reverseMethodMapping.get(methodName);
                execRef.setSimpleName(originalName);
                System.out.println("Replaced method reference: " + methodName + " -> " + originalName);
            }
        }
    }

    /**
     * Processor to handle method names in method bodies, including lambda expressions
     * and nested method calls that might not be caught by other processors.
     */
    private static class MethodAccessInBodyDeobfuscator extends AbstractProcessor<CtMethod<?>> {
        private final Map<String, String> reverseMethodMapping;
        
        public MethodAccessInBodyDeobfuscator(Map<String, String> reverseMethodMapping) {
            this.reverseMethodMapping = reverseMethodMapping;
        }
        
        @Override
        public void process(CtMethod<?> method) {
            if (method.getBody() == null) {
                return;
            }

            // Process the body as a string representation to find potential method references
            String body = method.getBody().toString();
            boolean hasObfuscatedMethods = false;
            
            for (String obfuscatedMethod : reverseMethodMapping.keySet()) {
                if (body.contains(obfuscatedMethod)) {
                    hasObfuscatedMethods = true;
                    System.out.println("Method body of " + method.getSimpleName() + 
                                      " contains potential obfuscated method: " + obfuscatedMethod);
                }
            }
            
            if (hasObfuscatedMethods) {
                // Log that we found potential obfuscated methods but didn't replace directly
                System.out.println("Note: Some obfuscated methods in " + method.getSimpleName() + 
                                  " may require special handling. Direct string replacement is disabled.");
            }
        }
    }

    /**
     * Processor to replace obfuscated field names with original names in field accesses
     */
    private static class FieldAccessDeobfuscator extends AbstractProcessor<CtFieldAccess<?>> {
        private final Map<String, Map<String, String>> reverseFieldMapping;

        public FieldAccessDeobfuscator(Map<String, Map<String, String>> reverseFieldMapping) {
            this.reverseFieldMapping = reverseFieldMapping;
        }

        @Override
        public void process(CtFieldAccess<?> fieldAccess) {
            CtFieldReference<?> fieldRef = fieldAccess.getVariable();
            String fieldName = fieldRef.getSimpleName();

            // Skip if there's no declaring type (which shouldn't happen for a field access)
            if (fieldRef.getDeclaringType() == null) {
                return;
            }

            String className = fieldRef.getDeclaringType().getQualifiedName();

            // Look for the class in our field mapping
            if (reverseFieldMapping.containsKey(className)) {
                Map<String, String> fieldsForClass = reverseFieldMapping.get(className);

                // Check if this field name is in the mapping
                if (fieldsForClass.containsKey(fieldName)) {
                    String originalName = fieldsForClass.get(fieldName);
                    fieldRef.setSimpleName(originalName);
                    System.out.println("Replaced field access: " + fieldName + " -> " + originalName +
                                      " in class " + className);
                }
            }
        }
    }
}
