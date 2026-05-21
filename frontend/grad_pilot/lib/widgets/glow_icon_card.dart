import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import 'glass_card.dart';

class GlowIconCard extends StatelessWidget {
  const GlowIconCard({
    super.key,
    required this.icon,
  });

  final IconData icon;

  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(18),
        boxShadow: const [
          BoxShadow(
            color: Color(0x226D5DFB),
            blurRadius: 22,
            offset: Offset(0, 10),
          ),
        ],
      ),
      child: GlassCard(
        padding: const EdgeInsets.all(12),
        borderRadius: 18,
        child: Icon(
          icon,
          color: AppColors.textPrimary,
          size: 20,
        ),
      ),
    );
  }
}
