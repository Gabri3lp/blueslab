import 'package:flutter/material.dart';

import '../features/home/home_screen.dart';
import 'app_theme.dart';

class BlueLabApp extends StatelessWidget {
  const BlueLabApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Blue Lab Calculator',
      debugShowCheckedModeBanner: false,
      theme: buildBlueLabTheme(),
      home: const HomeScreen(),
    );
  }
}
