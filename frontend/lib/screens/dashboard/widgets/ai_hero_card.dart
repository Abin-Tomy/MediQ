// AI Hero Card
// Replace this placeholder with the full widget from the conversation if needed.
// This file was generated for download.

import 'package:flutter/material.dart';

class AIHeroCard extends StatelessWidget {
  final String userName;
  final int wellnessScore;
  final String insight;
  final VoidCallback? onStart;

  const AIHeroCard({
    super.key,
    required this.userName,
    this.wellnessScore = 92,
    this.insight = 'Your wellness score improved by 6% this week. Keep it up!',
    this.onStart,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: const LinearGradient(
          colors: [Color(0xFF2F80ED), Color(0xFF56CCF2)],
        ),
        borderRadius: BorderRadius.circular(32),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('AI HEALTH ASSISTANT', style: TextStyle(color: Colors.white,fontWeight: FontWeight.bold)),
          const SizedBox(height:16),
          Text('Good Morning, $userName 👋',
              style: const TextStyle(color: Colors.white,fontSize:28,fontWeight: FontWeight.bold)),
          const SizedBox(height:12),
          Text(insight,style: const TextStyle(color: Colors.white70)),
          const SizedBox(height:20),
          Row(
            children:[
              const Expanded(child: _Metric('💤','7.5 hrs','Sleep')),
              SizedBox(width:8),
              const Expanded(child: _Metric('💧','5 / 8','Water')),
              SizedBox(width:8),
              const Expanded(child: _Metric('❤️','72 bpm','Heart')),
              SizedBox(width:12),
              CircleAvatar(radius:42,backgroundColor: Colors.white24,
                child: Text('$wellnessScore%',style: const TextStyle(color: Colors.white,fontWeight: FontWeight.bold))),
            ],
          ),
          const SizedBox(height:20),
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed:onStart,
              icon: const Icon(Icons.auto_awesome),
              label: const Text('Start AI Analysis'),
            ),
          )
        ],
      ),
    );
  }
}

class _Metric extends StatelessWidget{
  final String emoji,value,label;
  const _Metric(this.emoji,this.value,this.label);
  @override
  Widget build(BuildContext context){
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(color: Colors.white12,borderRadius: BorderRadius.circular(16)),
      child: Column(children:[
        Text(emoji,style: const TextStyle(fontSize:20)),
        Text(value,style: const TextStyle(color: Colors.white,fontWeight: FontWeight.bold)),
        Text(label,style: const TextStyle(color: Colors.white70,fontSize:12)),
      ]),
    );
  }
}
