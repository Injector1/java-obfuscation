package com.obfuscationdemo;

import spoon.Launcher;
import spoon.processing.AbstractProcessor;
import spoon.reflect.declaration.*;
import spoon.reflect.code.*;
import spoon.reflect.factory.Factory;
import spoon.reflect.reference.CtExecutableReference;
import spoon.reflect.reference.CtTypeReference;
import spoon.reflect.reference.CtVariableReference;
import spoon.reflect.reference.CtFieldReference;
import spoon.reflect.visitor.filter.TypeFilter;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.ObjectOutputStream;
import java.io.Serializable;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;

public class Obfuscator {
    // File to store obfuscation mappings
    private static final String MAPPING_FILE = "build/obfuscation-mapping.ser";

    private static final Map<String, String> methodNameMapping = new HashMap<>();
    private static final Map<String, Map<String, String>> parameterNameMapping = new HashMap<>();
    private static final Map<String, Map<String, String>> localVarNameMapping = new HashMap<>();
    private static final Map<String, Map<String, String>> fieldNameMapping = new HashMap<>();

    public static void main(String[] args) {
        String inputDir = args.length > 0 ? args[0] : "src/main/java/source";
        String outputDir = args.length > 1 ? args[1] : "src/main/java-obfuscated";
        String mode = args.length > 2 ? args[2] : "all";

        System.out.println("Starting obfuscation process...");
        System.out.println("Input directory: " + inputDir);
        System.out.println("Output directory: " + outputDir);
        System.out.println("Obfuscation mode: " + mode);

        switch (mode) {
            case "names":
                runNameObfuscation(inputDir, outputDir);
                break;
            case "bodies":
                runBodyRemovalObfuscation(inputDir, outputDir);
                break;
            case "all":
            default:
                runAllObfuscations(inputDir, outputDir);
                break;
        }

        System.out.println("Obfuscation completed! Output saved to: " + outputDir);
    }

    /**
     * Run only name obfuscation (methods, parameters, local variables)
     */
    private static void runNameObfuscation(String inputDir, String outputDir) {
        Launcher launcher = new Launcher();

        launcher.setSourceOutputDirectory(outputDir);
        launcher.addInputResource(inputDir);

        // Reset the mappings before starting a new obfuscation
        methodNameMapping.clear();
        parameterNameMapping.clear();
        localVarNameMapping.clear();
        fieldNameMapping.clear();

        launcher.addProcessor(new MethodNameObfuscationProcessor(methodNameMapping));
        launcher.addProcessor(new MethodInvocationProcessor(methodNameMapping));
        launcher.addProcessor(new ParameterNameProcessor());
        launcher.addProcessor(new LocalVariableProcessor());
        launcher.addProcessor(new FieldNameProcessor());
        launcher.addProcessor(new CommentRemovalProcessor());

        launcher.run();
        saveMappings();
    }

    /**
     * Save all obfuscation mappings to a file for later deobfuscation
     */
    private static void saveMappings() {
        ObfuscationMappings mappings = new ObfuscationMappings(
            methodNameMapping,
            parameterNameMapping,
            localVarNameMapping,
            fieldNameMapping
        );

        try {
            File file = new File(MAPPING_FILE);
            file.getParentFile().mkdirs();

            try (FileOutputStream fos = new FileOutputStream(file);
                 ObjectOutputStream oos = new ObjectOutputStream(fos)) {
                oos.writeObject(mappings);
                System.out.println("Obfuscation mappings saved to: " + file.getAbsolutePath());
            }
        } catch (IOException e) {
            System.err.println("Error saving obfuscation mappings: " + e.getMessage());
            e.printStackTrace();
        }
    }

    /**
     * Container class to hold all obfuscation mappings
     */
    public static class ObfuscationMappings implements Serializable {
        private static final long serialVersionUID = 1L;

        private final Map<String, String> methodMappings;
        private final Map<String, Map<String, String>> parameterMappings;
        private final Map<String, Map<String, String>> localVarMappings;
        private final Map<String, String> typeMappings;
        private final Map<String, Map<String, String>> fieldMappings;

        public ObfuscationMappings(
                Map<String, String> methodMappings,
                Map<String, Map<String, String>> parameterMappings,
                Map<String, Map<String, String>> localVarMappings,
                Map<String, Map<String, String>> fieldMappings) {
            this.methodMappings = methodMappings;
            this.parameterMappings = parameterMappings;
            this.localVarMappings = localVarMappings;
            this.typeMappings = new HashMap<>();
            this.fieldMappings = fieldMappings;
        }

        public Map<String, String> getMethodMappings() {
            return methodMappings;
        }

        public Map<String, Map<String, String>> getParameterMappings() {
            return parameterMappings;
        }

        public Map<String, Map<String, String>> getLocalVarMappings() {
            return localVarMappings;
        }

        public Map<String, String> getTypeMappings() {
            return typeMappings;
        }

        public Map<String, Map<String, String>> getFieldMappings() {
            return fieldMappings;
        }
    }

    /**
     * Run name obfuscation + method body removal
     */
    private static void runBodyRemovalObfuscation(String inputDir, String outputDir) {
        Launcher launcher = new Launcher();

        launcher.setSourceOutputDirectory(outputDir);
        launcher.addInputResource(inputDir);
        launcher.addProcessor(new MethodBodyRemovalProcessor());

        launcher.run();
    }

    /**
     * Run all available obfuscations
     */
    private static void runAllObfuscations(String inputDir, String outputDir) {
        // First run name obfuscation
        runNameObfuscation(inputDir, outputDir);

        // Then run method body removal on the already obfuscated code
        Launcher launcher = new Launcher();
        launcher.setSourceOutputDirectory(outputDir);
        launcher.addInputResource(outputDir);
        launcher.addProcessor(new MethodBodyRemovalProcessor());
        launcher.run();
    }

    /**
     * Processor to rename method names
     */
    private static class MethodNameObfuscationProcessor extends AbstractProcessor<CtMethod<?>> {
        private final Random random = new Random();
        private final Map<String, String> nameMapping;

        public MethodNameObfuscationProcessor(Map<String, String> nameMapping) {
            this.nameMapping = nameMapping;
        }

        @Override
        public void process(CtMethod<?> method) {
            String originalName = method.getSimpleName();

            // Skip main method
            if (originalName.equals("main")) {
                return;
            }

            String obfuscatedName;
            // If we have already obfuscated a method with this name, reuse the obfuscated name
            if (nameMapping.containsKey(originalName)) {
                obfuscatedName = nameMapping.get(originalName);
            } else {
                // Otherwise, generate a new obfuscated name and store it
                obfuscatedName = generateObfuscatedName();
                nameMapping.put(originalName, obfuscatedName);
            }

            // Set the new obfuscated name for the method
            method.setSimpleName(obfuscatedName);
        }

        private String generateObfuscatedName() {
            StringBuilder name = new StringBuilder("m");
            int length = 5 + random.nextInt(10);
            for (int i = 0; i < length; i++) {
                name.append((char) ('a' + random.nextInt(26)));
            }
            return name.toString();
        }
    }

    /**
     * Processor to update method invocations to use the obfuscated names
     */
    private static class MethodInvocationProcessor extends AbstractProcessor<CtInvocation<?>> {
        private final Map<String, String> methodNameMapping;

        public MethodInvocationProcessor(Map<String, String> methodNameMapping) {
            this.methodNameMapping = methodNameMapping;
        }

        @Override
        public void process(CtInvocation<?> invocation) {
            CtExecutableReference<?> execRef = invocation.getExecutable();
            String methodName = execRef.getSimpleName();

            if (methodNameMapping.containsKey(methodName)) {
                // If the method's declaration is found in the processed source, it's safe to rename.
                if (execRef.getDeclaration() != null) {
                    execRef.setSimpleName(methodNameMapping.get(methodName));
                    return;
                }

                // If the declaration is not found, it could be a library method, or it could be
                // one of our own methods that was renamed, breaking the reference.
                // We use a heuristic based on package names to avoid renaming library calls.
                CtTypeReference<?> declaringType = execRef.getDeclaringType();
                if (declaringType != null) {
                    String qualifiedName = declaringType.getQualifiedName();
                    if (qualifiedName.startsWith("java.") || qualifiedName.startsWith("javax.")) {
                        // This is likely a JDK library call, so we don't touch it.
                        return;
                    }
                }

                // If it's not a known library package, we assume it's our code and rename the invocation.
                execRef.setSimpleName(methodNameMapping.get(methodName));
            }
        }
    }

    /**
     * Processor specifically for handling method parameters
     */
    private static class ParameterNameProcessor extends AbstractProcessor<CtParameter<?>> {
        private final Random random = new Random();

        @Override
        public void process(CtParameter<?> parameter) {
            if (isMainMethodParameter(parameter)) {
                return;
            }

            CtExecutable<?> method = parameter.getParent(CtExecutable.class);
            if (method == null) {
                return;
            }

            String methodSignature = method.getSignature();
            String originalName = parameter.getSimpleName();

            parameterNameMapping.putIfAbsent(methodSignature, new HashMap<>());
            Map<String, String> paramMapping = parameterNameMapping.get(methodSignature);

            if (!paramMapping.containsKey(originalName)) {
                String obfuscatedName = generateObfuscatedName();
                paramMapping.put(originalName, obfuscatedName);
            }

            String obfuscatedName = paramMapping.get(originalName);
            parameter.setSimpleName(obfuscatedName);

            CtBlock<?> body = null;
            if (method instanceof CtMethod) {
                body = ((CtMethod<?>) method).getBody();
            } else if (method instanceof CtConstructor) {
                body = ((CtConstructor<?>) method).getBody();
            }

            if (body != null) {
                for (CtVariableReference<?> reference : body.getElements(new TypeFilter<>(CtVariableReference.class))) {
                    if (reference.getSimpleName().equals(originalName)) {
                        reference.setSimpleName(obfuscatedName);
                    }
                }
            }
        }

        private boolean isMainMethodParameter(CtParameter<?> parameter) {
            CtExecutable<?> method = parameter.getParent(CtExecutable.class);
            return method != null && method.getSimpleName().equals("main");
        }

        private String generateObfuscatedName() {
            StringBuilder name = new StringBuilder("p");
            int length = 5 + random.nextInt(10);
            for (int i = 0; i < length; i++) {
                name.append((char) ('a' + random.nextInt(26)));
            }
            return name.toString();
        }
    }

    /**
     * Processor specifically for handling local variables including loop variables
     */
    private static class LocalVariableProcessor extends AbstractProcessor<CtLocalVariable<?>> {
        private final Random random = new Random();

        @Override
        public void process(CtLocalVariable<?> localVar) {
            CtExecutable<?> method = localVar.getParent(CtExecutable.class);
            if (method == null) {
                return;
            }

            String methodSignature = method.getSignature();
            String originalName = localVar.getSimpleName();

            localVarNameMapping.putIfAbsent(methodSignature, new HashMap<>());
            Map<String, String> varMapping = localVarNameMapping.get(methodSignature);

            if (!varMapping.containsKey(originalName)) {
                String obfuscatedName = generateObfuscatedName();
                varMapping.put(originalName, obfuscatedName);
            }

            String obfuscatedName = varMapping.get(originalName);
            localVar.setSimpleName(obfuscatedName);

            CtBlock<?> body = null;
            if (method instanceof CtMethod) {
                body = ((CtMethod<?>) method).getBody();
            } else if (method instanceof CtConstructor) {
                body = ((CtConstructor<?>) method).getBody();
            }

            if (body != null) {
                for (CtVariableReference<?> reference : body.getElements(new TypeFilter<>(CtVariableReference.class))) {
                    if (reference.getSimpleName().equals(originalName)) {
                        reference.setSimpleName(obfuscatedName);
                    }
                }

                for (CtFor forLoop : body.getElements(new TypeFilter<>(CtFor.class))) {
                    if (forLoop.getExpression() != null) {
                        handleExpressionRenaming(forLoop.getExpression(), originalName, obfuscatedName);
                    }

                    if (forLoop.getForUpdate() != null) {
                        for (CtStatement update : forLoop.getForUpdate()) {
                            if (update instanceof CtExpression) {
                                handleExpressionRenaming((CtExpression<?>) update, originalName, obfuscatedName);
                            }
                        }
                    }
                }
            }
        }

        /**
         * Helper method to handle renaming variables in expressions
         */
        private void handleExpressionRenaming(CtExpression<?> expression, String originalName, String obfuscatedName) {
            if (expression instanceof CtBinaryOperator) {
                CtBinaryOperator<?> binary = (CtBinaryOperator<?>) expression;

                handleExpressionRenaming(binary.getLeftHandOperand(), originalName, obfuscatedName);
                handleExpressionRenaming(binary.getRightHandOperand(), originalName, obfuscatedName);
            }
            else if (expression instanceof CtUnaryOperator) {
                CtUnaryOperator<?> unary = (CtUnaryOperator<?>) expression;
                handleExpressionRenaming(unary.getOperand(), originalName, obfuscatedName);
            }
            else if (expression instanceof CtVariableAccess) {
                CtVariableAccess<?> access = (CtVariableAccess<?>) expression;
                if (access.getVariable().getSimpleName().equals(originalName)) {
                    access.getVariable().setSimpleName(obfuscatedName);
                }
            }
        }

        private String generateObfuscatedName() {
            StringBuilder name = new StringBuilder("l");
            int length = 5 + random.nextInt(10);
            for (int i = 0; i < length; i++) {
                name.append((char) ('a' + random.nextInt(26)));
            }
            return name.toString();
        }
    }

    /**
     * Processor specifically for handling class fields/properties
     */
    private static class FieldNameProcessor extends AbstractProcessor<CtField<?>> {
        private final Random random = new Random();

        @Override
        public void process(CtField<?> field) {
            // Get the class containing this field
            CtType<?> declaringType = field.getDeclaringType();
            if (declaringType == null) {
                return;
            }

            // Skip static final fields (likely constants)
            if (field.isStatic() && field.isFinal()) {
                return;
            }

            String className = declaringType.getQualifiedName();
            String originalName = field.getSimpleName();

            // Initialize mapping for this class if it doesn't exist
            fieldNameMapping.putIfAbsent(className, new HashMap<>());
            Map<String, String> classFieldMapping = fieldNameMapping.get(className);

            // Generate or reuse obfuscated name
            if (!classFieldMapping.containsKey(originalName)) {
                String obfuscatedName = generateObfuscatedName();
                classFieldMapping.put(originalName, obfuscatedName);
            }

            String obfuscatedName = classFieldMapping.get(originalName);
            field.setSimpleName(obfuscatedName);

            // Find and update all field accesses in the class
            for (CtFieldReference<?> fieldRef : declaringType.getElements(new TypeFilter<>(CtFieldReference.class))) {
                if (fieldRef.getSimpleName().equals(originalName) && fieldRef.getDeclaringType() != null &&
                    fieldRef.getDeclaringType().getQualifiedName().equals(className)) {
                    fieldRef.setSimpleName(obfuscatedName);
                }
            }
        }

        private String generateObfuscatedName() {
            StringBuilder name = new StringBuilder("f");
            int length = 5 + random.nextInt(10);
            for (int i = 0; i < length; i++) {
                name.append((char) ('a' + random.nextInt(26)));
            }
            return name.toString();
        }
    }

    /**
     * Processor to remove all comments (including JavaDoc, line comments, block comments)
     */
    private static class CommentRemovalProcessor extends AbstractProcessor<CtElement> {

        @Override
        public void process(CtElement element) {
            // Remove all comments from the element
            element.setComments(new java.util.ArrayList<>());
        }
    }

    /**
     * Processor to remove method bodies but keep JavaDoc
     */
    private static class MethodBodyRemovalProcessor extends AbstractProcessor<CtMethod<?>> {

        @Override
        public void process(CtMethod<?> method) {
            if (method.getSimpleName().equals("main")) {
                return;
            }

            Factory factory = getFactory();
            CtBlock<?> emptyBlock = factory.createBlock();

            if (!method.getType().toString().equals("void")) {
                CtReturn<Object> returnStmt = factory.createReturn();

                String typeName = method.getType().toString();
                if (typeName.equals("int") || typeName.equals("long") || typeName.equals("short") || typeName.equals("byte")) {
                    returnStmt.setReturnedExpression(factory.createLiteral(0));
                } else if (typeName.equals("float") || typeName.equals("double")) {
                    returnStmt.setReturnedExpression(factory.createLiteral(0.0));
                } else if (typeName.equals("boolean")) {
                    returnStmt.setReturnedExpression(factory.createLiteral(false));
                } else if (typeName.equals("char")) {
                    returnStmt.setReturnedExpression(factory.createLiteral('\0'));
                } else if (!typeName.equals("void")) {
                    returnStmt.setReturnedExpression(factory.createLiteral(null));
                }

                emptyBlock.addStatement(returnStmt);
            }
            method.setBody(emptyBlock);
        }
    }
}
