package com.obfuscationdemo;

import spoon.Launcher;
import spoon.processing.AbstractProcessor;
import spoon.reflect.declaration.*;
import spoon.reflect.code.*;
import spoon.reflect.factory.Factory;
import spoon.reflect.reference.CtExecutableReference;
import spoon.reflect.reference.CtVariableReference;
import spoon.reflect.visitor.filter.TypeFilter;

import java.util.HashMap;
import java.util.Map;
import java.util.Random;

public class Obfuscator {

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

        Map<String, String> methodNameMapping = new HashMap<>();

        launcher.addProcessor(new MethodNameObfuscationProcessor(methodNameMapping));
        launcher.addProcessor(new MethodInvocationProcessor(methodNameMapping));
        launcher.addProcessor(new ParameterNameProcessor());
        launcher.addProcessor(new LocalVariableProcessor());

        launcher.run();
    }

    /**
     * Run name obfuscation + method body removal
     */
    private static void runBodyRemovalObfuscation(String inputDir, String outputDir) {
        Launcher launcher = new Launcher();

        launcher.setSourceOutputDirectory(outputDir);
        launcher.addInputResource(inputDir);

        Map<String, String> methodNameMapping = new HashMap<>();

        launcher.addProcessor(new MethodNameObfuscationProcessor(methodNameMapping));
        launcher.addProcessor(new MethodInvocationProcessor(methodNameMapping));
        launcher.addProcessor(new ParameterNameProcessor());
        launcher.addProcessor(new LocalVariableProcessor());

        launcher.addProcessor(new MethodBodyRemovalProcessor());

        launcher.run();
    }

    /**
     * Run all available obfuscations
     */
    private static void runAllObfuscations(String inputDir, String outputDir) {
        runBodyRemovalObfuscation(inputDir, outputDir);
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

            if (originalName.equals("main") || nameMapping.containsKey(originalName)) {
                return;
            }

            String obfuscatedName = generateObfuscatedName();
            nameMapping.put(originalName, obfuscatedName);

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

            if (!methodNameMapping.containsKey(methodName)) {
                return;
            }

            String obfuscatedName = methodNameMapping.get(methodName);
            execRef.setSimpleName(obfuscatedName);
        }
    }

    /**
     * Processor specifically for handling method parameters
     */
    private static class ParameterNameProcessor extends AbstractProcessor<CtParameter<?>> {
        private final Random random = new Random();
        private final Map<String, Map<String, String>> methodToParamMappings = new HashMap<>();

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

            methodToParamMappings.putIfAbsent(methodSignature, new HashMap<>());
            Map<String, String> paramMapping = methodToParamMappings.get(methodSignature);

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
        private final Map<String, Map<String, String>> methodToVarMappings = new HashMap<>();

        @Override
        public void process(CtLocalVariable<?> localVar) {
            CtExecutable<?> method = localVar.getParent(CtExecutable.class);
            if (method == null) {
                return;
            }

            String methodSignature = method.getSignature();
            String originalName = localVar.getSimpleName();

            methodToVarMappings.putIfAbsent(methodSignature, new HashMap<>());
            Map<String, String> varMapping = methodToVarMappings.get(methodSignature);

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

            for (CtComment comment : method.getComments()) {
                if (comment.getCommentType() == CtComment.CommentType.JAVADOC) {
                    emptyBlock.addComment(comment.clone());
                }
            }

            method.setBody(emptyBlock);
        }
    }
}
