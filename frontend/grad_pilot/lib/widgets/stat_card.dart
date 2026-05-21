import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import 'glass_card.dart';

class StatCard extends StatelessWidget {
  const StatCard({
    super.key,
    required this.label,
    required this.value,
    required this.icon,
    this.compact = false,
  });

  final String label;
  final String value;
  final IconData icon;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return GlassCard(
      padding: EdgeInsets.all(compact ? 14 : 16),
      borderRadius: compact ? 20 : 22,
      child: Column(
        crossAxisAlignment:
            compact ? CrossAxisAlignment.center : CrossAxisAlignment.start,
        children: [
          Container(
            height: compact ? 38 : 42,
            width: compact ? 38 : 42,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(14),
              gradient: AppColors.primaryGradient,
            ),
            child: Icon(
              icon,
              color: AppColors.textPrimary,
              size: compact ? 18 : 20,
            ),
          ),
          SizedBox(height: compact ? 12 : 14),
          Text(
            value,
            style: textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.w800,
              fontSize: compact ? 22 : 28,
            ),
          ),
          SizedBox(height: compact ? 4 : 6),
          Text(
            label,
            textAlign: compact ? TextAlign.center : TextAlign.start,
            style: textTheme.bodyMedium?.copyWith(
              color: AppColors.textSecondary,
              fontSize: compact ? 12 : null,
            ),
          ),
        ],
      ),
    );
  }
}
