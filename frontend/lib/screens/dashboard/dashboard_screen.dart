import 'package:flutter/material.dart';



import 'widgets/dashboard_header.dart';
import 'widgets/dashboard_search_bar.dart';
import 'widgets/ai_hero_card.dart';
import 'widgets/health_snapshot.dart';
import 'widgets/appointment_card.dart';
import 'widgets/quick_actions_grid.dart';
import 'widgets/daily_tip_card.dart';
import 'widgets/dashboard_bottom_nav.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {

  int currentIndex = 0;

  @override
  Widget build(BuildContext context) {

    return Scaffold(

      backgroundColor: const Color(0xffF8FAFC),

      bottomNavigationBar: DashboardBottomNav(
        currentIndex: currentIndex,
        onTap: (index) {
          setState(() {
            currentIndex = index;
          });
        },
      ),

      body: SafeArea(

        child: SingleChildScrollView(

          physics: const BouncingScrollPhysics(),

          padding: const EdgeInsets.fromLTRB(
            24,
            20,
            24,
            30,
          ),

          child: Column(

            crossAxisAlignment: CrossAxisAlignment.start,

            children: [

              //-------------------------------------------------------
              // HEADER
              //-------------------------------------------------------

              const DashboardHeader(
                userName: "Vishnu Prasad",
              ),

              const SizedBox(height: 28),

              //-------------------------------------------------------
              // AI HERO
              //-------------------------------------------------------

              AIHeroCard(
                userName: "Vishnu",
                onStart: () {

                  /// Later

                  /// Navigate to Symptom Checker

                },
              ),

              const SizedBox(height: 28),

              //-------------------------------------------------------
              // SEARCH
              //-------------------------------------------------------

              DashboardSearchBar(
                onTap: () {},
              ),

              const SizedBox(height: 34),

              //-------------------------------------------------------
              // HEALTH
              //-------------------------------------------------------

              const HealthSnapshot(),

              const SizedBox(height: 34),

              //-------------------------------------------------------
              // APPOINTMENT
              //-------------------------------------------------------

              const AppointmentCard(),

              const SizedBox(height: 34),

              //-------------------------------------------------------
              // QUICK ACTIONS
              //-------------------------------------------------------

              const QuickActionsGrid(),

              const SizedBox(height: 34),

              //-------------------------------------------------------
              // DAILY TIP
              //-------------------------------------------------------

              const DailyTipCard(),

              const SizedBox(height: 40),

            ],
          ),
        ),
      ),
    );
  }
}