import 'package:flutter/material.dart';

class BodyArea {
  final String name;
  final IconData icon;
  const BodyArea({required this.name, required this.icon});

  static const items = <BodyArea>[
    BodyArea(name:'Head', icon: Icons.psychology_alt_rounded),
    BodyArea(name:'Chest', icon: Icons.favorite_rounded),
    BodyArea(name:'Abdomen', icon: Icons.monitor_heart_outlined),
    BodyArea(name:'Arms', icon: Icons.accessibility_new_rounded),
    BodyArea(name:'Legs', icon: Icons.directions_walk_rounded),
    BodyArea(name:'Skin', icon: Icons.spa_outlined),
  ];
}
