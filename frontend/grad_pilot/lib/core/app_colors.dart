import 'package:flutter/material.dart';

class AppColors {
  const AppColors._();

  static const background = Color(0xFF050816);
  static const background2 = Color(0xFF07111F);
  static const surface = Color(0xFF0D1B2E);
  static const card = Color(0xFF13233A);
  static const primary = Color(0xFF6D5DFB);
  static const primaryLight = Color(0xFF8B7CFF);
  static const secondary = Color(0xFF38BDF8);
  static const accent = Color(0xFFA78BFA);
  static const textPrimary = Color(0xFFF8FAFC);
  static const textSecondary = Color(0xFFCBD5E1);
  static const muted = Color(0xFF64748B);
  static const border = Color(0xFF25324A);

  static const backgroundGradient = LinearGradient(
    begin: Alignment.topCenter,
    end: Alignment.bottomCenter,
    colors: [
      background,
      background2,
      background,
    ],
  );

  static const primaryGradient = LinearGradient(
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
    colors: [
      primary,
      secondary,
    ],
  );

  static const heroGlowGradient = RadialGradient(
    center: Alignment.center,
    radius: 0.9,
    colors: [
      Color(0x446D5DFB),
      Color(0x2238BDF8),
      Color(0x00050816),
    ],
  );
}
