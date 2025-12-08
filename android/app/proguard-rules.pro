# Anti-Gravity Stealth Layer Rules

# Keep Capacitor
-keep class com.getcapacitor.** { *; }
-keep interface com.getcapacitor.** { *; }

# Keep Firebase
-keep class com.google.firebase.** { *; }

# Protect Nexus Bridges
-keep class com.nexus.ai.Bridge.** { *; }

# Obfuscate everything else
-repackageclasses 'a.b.c'
-allowaccessmodification
-optimizations !code/simplification/arithmetic,!field/*,!class/merging/*

# Hide Logging
-assumenosideeffects class android.util.Log {
    public static boolean isLoggable(java.lang.String, int);
    public static int v(...);
    public static int i(...);
    public static int w(...);
    public static int d(...);
    public static int e(...);
}
