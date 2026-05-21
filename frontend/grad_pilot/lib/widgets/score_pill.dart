import 'package:flutter/material.dart';

import '../core/app_colors.dart';

class ScorePill extends StatelessWidget {
  const ScorePill({
    super.key,
    required this.label,
    required this.value,
    this.icon,
  });

  final String label;
  final Object? value;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final displayValue = _formatValue(value);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.surface.withValues(alpha: 0.86),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: AppColors.border.withValues(alpha: 0.92)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (icon != null) ...[
            Icon(icon, size: 15, color: AppColors.secondary),
            const SizedBox(width: 7),
          ],
          Text(
            displayValue,
            style: textTheme.bodyMedium?.copyWith(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(width: 8),
          Text(
            label,
            style: textTheme.bodySmall?.copyWith(
              color: AppColors.muted,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

  String _formatValue(Object? rawValue) {
    if (rawValue == null) {
      return '--';
    }
    if (rawValue is double) {
      return rawValue.toStringAsFixed(1);
    }
    if (rawValue is num) {
      return rawValue.toString();
    }
    final text = rawValue.toString().trim();
    return text.isEmpty ? '--' : text;
  }
}
