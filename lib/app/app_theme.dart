import 'package:flutter/material.dart';

ThemeData buildBlueLabTheme() {
  return ThemeData(
    brightness: Brightness.light,
    scaffoldBackgroundColor: const Color(0xFFE8F0FE),
    cardColor: const Color(0xFFFFFFFF),
    dividerColor: const Color(0xFFB0C4DE),
    colorScheme: const ColorScheme.light(
      primary: Color(0xFF1A56A8),
      secondary: Color(0xFF3D7AB8),
      surface: Color(0xFFFFFFFF),
      onSurface: Color(0xFF1A2A3A),
    ),
    useMaterial3: true,
  );
}
