# This configuration provides aggressive obfuscation while keeping the application functional

# Keep only the main method entry point
-keep class * {
    public static void main(java.lang.String[]);
}

# Aggressive optimization and obfuscation settings
-optimizations !code/simplification/arithmetic,!code/simplification/cast,!field/*,!class/merging/*
-optimizationpasses 5
-allowaccessmodification
-repackageclasses ''
-overloadaggressively
-useuniqueclassmembernames

# String obfuscation and class name scrambling
-adaptclassstrings
-adaptresourcefilenames    **.properties,**.xml,**.txt,**.html,**.htm
-adaptresourcefilecontents **.properties,META-INF/MANIFEST.MF

# Remove debugging information
-keepattributes !LocalVariableTable,!LocalVariableTypeTable,!SourceFile,!LineNumberTable

# Only keep essential attributes for proper execution
-keepattributes Signature,RuntimeVisibleAnnotations,AnnotationDefault,StackMapTable

# Rename packages and classes aggressively
-flattenpackagehierarchy ''
-allowaccessmodification

# Control flow obfuscation
-optimizations !method/inlining/*

# Remove unused code
-dontshrink

-dontpreverify

# Verbose output for debugging
-verbose

# Suppress warnings
-dontwarn **
-ignorewarnings

-mergeinterfacesaggressively
-dontusemixedcaseclassnames

-keepclassmembers class * {
    native <methods>;
}

# Additional obfuscation for reflection-heavy code
-keepnames class * implements java.io.Serializable
-keepclassmembers class * implements java.io.Serializable {
    static final long serialVersionUID;
    private static final java.io.ObjectStreamField[] serialPersistentFields;
    !static !transient <fields>;
    private void writeObject(java.io.ObjectOutputStream);
    private void readObject(java.io.ObjectInputStream);
    java.lang.Object writeReplace();
    java.lang.Object readResolve();
}