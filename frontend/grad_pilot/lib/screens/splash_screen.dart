import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../core/app_colors.dart';
import '../core/app_config.dart';
import '../core/app_routes.dart';
import '../widgets/app_button.dart';
import '../widgets/glass_card.dart';
import '../widgets/glow_icon_card.dart';
import '../widgets/gradient_text.dart';

class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
        child: Stack(
          children: [
            const _DecorativeBackground(),
            SafeArea(
              child: Center(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(
                    horizontal: AppConfig.horizontalPadding,
                    vertical: 20,
                  ),
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(
                      maxWidth: AppConfig.contentMaxWidth,
                    ),
                    child: Column(
                      children: [
                        const SizedBox(height: 12),
                        const _HeroIconCluster()
                            .animate()
                            .fadeIn(duration: 550.ms, curve: Curves.easeOut)
                            .slideY(begin: 0.08, end: 0, duration: 550.ms)
                            .scale(
                              begin: const Offset(0.96, 0.96),
                              end: const Offset(1, 1),
                              duration: 550.ms,
                              curve: Curves.easeOutCubic,
                            ),
                        const SizedBox(height: 34),
                        Wrap(
                          alignment: WrapAlignment.center,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          spacing: 2,
                          children: [
                            Text(
                              'Grad',
                              style: textTheme.displaySmall?.copyWith(
                                fontSize: 38,
                                fontWeight: FontWeight.w800,
                                letterSpacing: -1.8,
                              ),
                            ),
                            GradientText(
                              text: 'Pilot',
                              style: textTheme.displaySmall?.copyWith(
                                fontSize: 38,
                                fontWeight: FontWeight.w800,
                                letterSpacing: -1.8,
                              ),
                              gradient: AppColors.primaryGradient,
                            ),
                          ],
                        )
                            .animate()
                            .fadeIn(
                              delay: 120.ms,
                              duration: 450.ms,
                              curve: Curves.easeOut,
                            )
                            .slideY(begin: 0.18, end: 0, duration: 450.ms),
                        const SizedBox(height: 12),
                        Text(
                          AppConfig.subtitle,
                          textAlign: TextAlign.center,
                          style: textTheme.titleMedium?.copyWith(
                            color: AppColors.textSecondary,
                            letterSpacing: 0.2,
                          ),
                        )
                            .animate()
                            .fadeIn(
                              delay: 220.ms,
                              duration: 420.ms,
                              curve: Curves.easeOut,
                            ),
                        const SizedBox(height: 16),
                        Text(
                          'Discover credible, buildable graduation projects with an AI-first research workflow designed for serious students.',
                          textAlign: TextAlign.center,
                          style: textTheme.bodyLarge?.copyWith(
                            color: AppColors.textSecondary.withValues(
                              alpha: 0.94,
                            ),
                          ),
                        )
                            .animate()
                            .fadeIn(
                              delay: 260.ms,
                              duration: 420.ms,
                              curve: Curves.easeOut,
                            ),
                        const SizedBox(height: 28),
                        GlassCard(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 18,
                            vertical: 18,
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                height: 42,
                                width: 42,
                                decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(14),
                                  gradient: AppColors.primaryGradient,
                                  boxShadow: const [
                                    BoxShadow(
                                      color: Color(0x226D5DFB),
                                      blurRadius: 16,
                                      spreadRadius: 2,
                                    ),
                                  ],
                                ),
                                child: const Icon(
                                  Icons.auto_awesome_rounded,
                                  color: AppColors.textPrimary,
                                  size: 22,
                                ),
                              ),
                              const SizedBox(width: 14),
                              Expanded(
                                child: Text(
                                  AppConfig.valueProposition,
                                  style: textTheme.bodyMedium?.copyWith(
                                    color: AppColors.textSecondary,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        )
                            .animate()
                            .fadeIn(
                              delay: 340.ms,
                              duration: 450.ms,
                              curve: Curves.easeOut,
                            )
                            .slideY(begin: 0.18, end: 0, duration: 450.ms),
                        const SizedBox(height: 28),
                        AppButton(
                          label: 'Get Started',
                          icon: Icons.rocket_launch_rounded,
                          onPressed: () {
                            Navigator.of(context).pushNamed(AppRoutes.login);
                          },
                        )
                            .animate()
                            .fadeIn(
                              delay: 430.ms,
                              duration: 430.ms,
                              curve: Curves.easeOut,
                            )
                            .slideY(begin: 0.16, end: 0, duration: 430.ms),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _HeroIconCluster extends StatelessWidget {
  const _HeroIconCluster();

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: 300,
      height: 250,
      child: Stack(
        clipBehavior: Clip.none,
        alignment: Alignment.center,
        children: [
          Container(
            width: 216,
            height: 216,
            decoration: const BoxDecoration(
              shape: BoxShape.circle,
              gradient: AppColors.heroGlowGradient,
            ),
          ),
          Container(
            width: 176,
            height: 176,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              border: Border.all(color: AppColors.border.withValues(alpha: 0.7)),
              color: AppColors.card.withValues(alpha: 0.68),
              boxShadow: const [
                BoxShadow(
                  color: Color(0x226D5DFB),
                  blurRadius: 36,
                  spreadRadius: 8,
                ),
              ],
            ),
          ),
          Container(
            width: 132,
            height: 132,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: const LinearGradient(
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
                colors: [
                  Color(0x446D5DFB),
                  Color(0x2238BDF8),
                ],
              ),
              border: Border.all(
                color: AppColors.primaryLight.withValues(alpha: 0.45),
              ),
            ),
            child: const Icon(
              Icons.school_rounded,
              size: 62,
              color: AppColors.textPrimary,
            ),
          ),
          const Positioned(
            top: 8,
            right: 28,
            child: GlowIconCard(icon: Icons.code_rounded),
          ),
          const Positioned(
            left: 12,
            top: 84,
            child: GlowIconCard(icon: Icons.account_tree_rounded),
          ),
          const Positioned(
            bottom: 18,
            right: 38,
            child: GlowIconCard(icon: Icons.menu_book_rounded),
          ),
        ],
      ),
    );
  }
}

class _DecorativeBackground extends StatelessWidget {
  const _DecorativeBackground();

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Stack(
        children: [
          Positioned(
            top: -60,
            right: -30,
            child: _BlurOrb(
              size: 180,
              color: AppColors.primary.withValues(alpha: 0.16),
            ),
          ),
          Positioned(
            left: -70,
            bottom: 120,
            child: _BlurOrb(
              size: 220,
              color: AppColors.secondary.withValues(alpha: 0.1),
            ),
          ),
          const Positioned(top: 110, left: 36, child: _Dot(size: 5)),
          const Positioned(top: 180, right: 54, child: _Dot(size: 3)),
          const Positioned(top: 290, left: 90, child: _Dot(size: 4)),
          const Positioned(bottom: 200, right: 70, child: _Dot(size: 5)),
          const Positioned(bottom: 120, left: 52, child: _Dot(size: 3)),
          Positioned(
            top: 140,
            right: 70,
            child: _Ring(
              size: 56,
              color: AppColors.primaryLight.withValues(alpha: 0.16),
            ),
          ),
          Positioned(
            bottom: 180,
            left: 24,
            child: _Ring(
              size: 72,
              color: AppColors.secondary.withValues(alpha: 0.12),
            ),
          ),
        ],
      ),
    );
  }
}

class _BlurOrb extends StatelessWidget {
  const _BlurOrb({
    required this.size,
    required this.color,
  });

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: color,
        boxShadow: [
          BoxShadow(
            color: color,
            blurRadius: 100,
            spreadRadius: 24,
          ),
        ],
      ),
    );
  }
}

class _Dot extends StatelessWidget {
  const _Dot({required this.size});

  final double size;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: const BoxDecoration(
        shape: BoxShape.circle,
        color: Color(0x88F8FAFC),
      ),
    );
  }
}

class _Ring extends StatelessWidget {
  const _Ring({
    required this.size,
    required this.color,
  });

  final double size;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        border: Border.all(color: color, width: 1),
      ),
    );
  }
}
