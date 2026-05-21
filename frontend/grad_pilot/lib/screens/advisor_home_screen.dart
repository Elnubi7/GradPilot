import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../core/app_colors.dart';
import '../core/app_config.dart';
import '../core/app_routes.dart';
import '../models/app_user.dart';
import '../widgets/app_button.dart';
import '../widgets/empty_state.dart';
import '../widgets/glass_card.dart';
import '../widgets/glow_icon_card.dart';
import '../widgets/stat_card.dart';

class AdvisorHomeScreen extends StatelessWidget {
  const AdvisorHomeScreen({
    super.key,
    required this.currentUser,
  });

  final AppUser? currentUser;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final firstName = _extractFirstName(currentUser?.fullName);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: AppConfig.contentMaxWidth),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'Hello, $firstName 👋',
                style: textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.w800,
                  fontSize: 30,
                ),
              )
                  .animate()
                  .fadeIn(duration: 420.ms)
                  .slideY(begin: 0.08, end: 0, duration: 420.ms),
              const SizedBox(height: 8),
              Text(
                'What would you like to build today?',
                style: textTheme.bodyLarge,
              )
                  .animate(delay: 80.ms)
                  .fadeIn(duration: 380.ms),
              const SizedBox(height: 22),
              GlassCard(
                padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
                borderRadius: 20,
                child: Row(
                  children: [
                    Icon(
                      Icons.search_rounded,
                      color: AppColors.textSecondary.withValues(alpha: 0.9),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Search projects, topics, skills...',
                        style: textTheme.bodyMedium?.copyWith(
                          color: AppColors.muted,
                        ),
                      ),
                    ),
                  ],
                ),
              )
                  .animate(delay: 120.ms)
                  .fadeIn(duration: 380.ms)
                  .slideY(begin: 0.08, end: 0, duration: 380.ms),
              const SizedBox(height: 22),
              GlassCard(
                padding: const EdgeInsets.all(22),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const _AdvisorHeroIcons(),
                    const SizedBox(height: 18),
                    Text(
                      'AI Project Advisor',
                      style: textTheme.headlineMedium?.copyWith(
                        fontWeight: FontWeight.w800,
                        fontSize: 30,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      'Generate verified graduation project ideas using AI, GitHub, and arXiv.',
                      style: textTheme.bodyLarge,
                    ),
                    const SizedBox(height: 18),
                    AppButton(
                      label: 'Generate Ideas',
                      icon: Icons.auto_awesome_rounded,
                      onPressed: () {
                        Navigator.of(context).pushNamed(AppRoutes.generateIdeas);
                      },
                    ),
                  ],
                ),
              )
                  .animate(delay: 180.ms)
                  .fadeIn(duration: 450.ms)
                  .slideY(begin: 0.08, end: 0, duration: 450.ms),
              const SizedBox(height: 22),
              LayoutBuilder(
                builder: (context, constraints) {
                  const stats = [
                    _AdvisorStatData(
                      label: 'Saved',
                      value: '0',
                      icon: Icons.bookmark_rounded,
                    ),
                    _AdvisorStatData(
                      label: 'Favorites',
                      value: '0',
                      icon: Icons.favorite_rounded,
                    ),
                    _AdvisorStatData(
                      label: 'Generated',
                      value: '0',
                      icon: Icons.auto_awesome_rounded,
                    ),
                  ];

                  if (constraints.maxWidth < 360) {
                    return SingleChildScrollView(
                      scrollDirection: Axis.horizontal,
                      child: Row(
                        children: [
                          for (var index = 0; index < stats.length; index++) ...[
                            SizedBox(
                              width: 112,
                              child: _AdvisorStat(data: stats[index]),
                            ),
                            if (index != stats.length - 1)
                              const SizedBox(width: 12),
                          ],
                        ],
                      ),
                    );
                  }

                  return Row(
                    children: [
                      for (var index = 0; index < stats.length; index++) ...[
                        Expanded(child: _AdvisorStat(data: stats[index])),
                        if (index != stats.length - 1)
                          const SizedBox(width: 12),
                      ],
                    ],
                  );
                },
              )
                  .animate(delay: 240.ms)
                  .fadeIn(duration: 420.ms),
              const SizedBox(height: 28),
              Text(
                'Recent',
                style: textTheme.titleMedium?.copyWith(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 14),
              const EmptyState(
                title: 'Generate your first project idea.',
                message:
                    'Use the AI advisor to turn your requirements into source-backed graduation concepts.',
                icon: Icons.rocket_launch_rounded,
              )
                  .animate(delay: 300.ms)
                  .fadeIn(duration: 400.ms)
                  .slideY(begin: 0.06, end: 0, duration: 400.ms),
            ],
          ),
        ),
      ),
    );
  }

  String _extractFirstName(String? fullName) {
    if (fullName == null || fullName.trim().isEmpty) {
      return 'Student';
    }
    return fullName.trim().split(RegExp(r'\s+')).first;
  }
}

class _AdvisorHeroIcons extends StatelessWidget {
  const _AdvisorHeroIcons();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 128,
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          Positioned(
            left: 0,
            top: 4,
            child: Container(
              height: 104,
              width: 104,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: AppColors.heroGlowGradient,
                border: Border.all(
                  color: AppColors.primaryLight.withValues(alpha: 0.25),
                ),
              ),
              child: const Icon(
                Icons.auto_awesome_rounded,
                color: AppColors.textPrimary,
                size: 44,
              ),
            ),
          ),
          const Positioned(
            left: 86,
            top: 8,
            child: GlowIconCard(icon: Icons.school_rounded),
          ),
          const Positioned(
            left: 68,
            bottom: 0,
            child: GlowIconCard(icon: Icons.hub_rounded),
          ),
        ],
      ),
    );
  }
}

class _AdvisorStat extends StatelessWidget {
  const _AdvisorStat({required this.data});

  final _AdvisorStatData data;

  @override
  Widget build(BuildContext context) {
    return StatCard(
      label: data.label,
      value: data.value,
      icon: data.icon,
      compact: true,
    );
  }
}

class _AdvisorStatData {
  const _AdvisorStatData({
    required this.label,
    required this.value,
    required this.icon,
  });

  final String label;
  final String value;
  final IconData icon;
}
