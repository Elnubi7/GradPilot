import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../core/app_colors.dart';
import '../core/app_config.dart';
import '../core/app_routes.dart';
import '../models/app_user.dart';
import '../services/api_service.dart';
import '../data/local_user_store.dart';
import '../widgets/app_button.dart';
import '../widgets/app_text_field.dart';
import '../widgets/glass_card.dart';
import '../widgets/glow_icon_card.dart';
import '../widgets/gradient_text.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen> {
  final _formKey = GlobalKey<FormState>();
  final _fullNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _departmentController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _userStore = const LocalUserStore();
  final _apiService = const ApiService();

  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;
  bool _isLoading = false;

  @override
  void dispose() {
    _fullNameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _departmentController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  Future<void> _handleRegister() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final AppUser registeredUser = await _apiService.register(
        fullName: _fullNameController.text,
        email: _emailController.text,
        phone: _phoneController.text,
        department: _departmentController.text,
        password: _passwordController.text,
        avatarStyle: 'blue',
      );
      await _userStore.saveCurrentUser(registeredUser);

      if (!mounted) {
        return;
      }

      Navigator.of(context).pushNamedAndRemoveUntil(
        AppRoutes.main,
        (route) => false,
      );
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.message)),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
        child: Stack(
          children: [
            const _RegisterBackground(),
            SafeArea(
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(
                  horizontal: AppConfig.horizontalPadding,
                  vertical: 20,
                ),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 430),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        IconButton(
                          onPressed: () => Navigator.of(context).maybePop(),
                          icon: const Icon(
                            Icons.arrow_back_rounded,
                            color: AppColors.textPrimary,
                          ),
                          style: IconButton.styleFrom(
                            backgroundColor:
                                AppColors.card.withValues(alpha: 0.5),
                            side: BorderSide(
                              color: AppColors.border.withValues(alpha: 0.8),
                            ),
                          ),
                        ),
                        const SizedBox(height: 22),
                        const _RegisterHero()
                            .animate()
                            .fadeIn(duration: 480.ms)
                            .slideY(begin: 0.08, end: 0, duration: 480.ms)
                            .scale(
                              begin: const Offset(0.97, 0.97),
                              end: const Offset(1, 1),
                              duration: 480.ms,
                            ),
                        const SizedBox(height: 24),
                        Text(
                          'Create Account',
                          style: textTheme.headlineMedium?.copyWith(
                            fontSize: 30,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Join GradPilot and get started',
                          style: textTheme.bodyLarge,
                        ),
                        const SizedBox(height: 24),
                        GlassCard(
                          padding: const EdgeInsets.all(22),
                          child: Form(
                            key: _formKey,
                            child: Column(
                              children: [
                                AppTextField(
                                  label: 'Full Name',
                                  hint: 'Enter your full name',
                                  controller: _fullNameController,
                                  prefixIcon: Icons.person_outline_rounded,
                                  textInputAction: TextInputAction.next,
                                  validator: _validateFullName,
                                ),
                                const SizedBox(height: 18),
                                AppTextField(
                                  label: 'Email',
                                  hint: 'you@example.com',
                                  controller: _emailController,
                                  prefixIcon: Icons.alternate_email_rounded,
                                  keyboardType: TextInputType.emailAddress,
                                  textInputAction: TextInputAction.next,
                                  validator: _validateEmail,
                                ),
                                const SizedBox(height: 18),
                                AppTextField(
                                  label: 'Phone Number',
                                  hint: '01xxxxxxxxx',
                                  controller: _phoneController,
                                  prefixIcon: Icons.phone_android_rounded,
                                  keyboardType: TextInputType.phone,
                                  textInputAction: TextInputAction.next,
                                  validator: _validatePhone,
                                ),
                                const SizedBox(height: 18),
                                AppTextField(
                                  label: 'Department',
                                  hint: 'Computer Science',
                                  controller: _departmentController,
                                  prefixIcon: Icons.account_tree_rounded,
                                  textInputAction: TextInputAction.next,
                                  validator: _validateRequired(
                                    'Department is required',
                                  ),
                                ),
                                const SizedBox(height: 18),
                                AppTextField(
                                  label: 'Password',
                                  hint: 'Create a password',
                                  controller: _passwordController,
                                  prefixIcon: Icons.lock_outline_rounded,
                                  obscureText: _obscurePassword,
                                  textInputAction: TextInputAction.next,
                                  validator: _validatePassword,
                                  suffixIcon: IconButton(
                                    onPressed: () {
                                      setState(() {
                                        _obscurePassword = !_obscurePassword;
                                      });
                                    },
                                    icon: Icon(
                                      _obscurePassword
                                          ? Icons.visibility_off_rounded
                                          : Icons.visibility_rounded,
                                      color: AppColors.textSecondary,
                                    ),
                                  ),
                                ),
                                const SizedBox(height: 18),
                                AppTextField(
                                  label: 'Confirm Password',
                                  hint: 'Re-enter your password',
                                  controller: _confirmPasswordController,
                                  prefixIcon: Icons.verified_user_outlined,
                                  obscureText: _obscureConfirmPassword,
                                  textInputAction: TextInputAction.done,
                                  validator: _validateConfirmPassword,
                                  suffixIcon: IconButton(
                                    onPressed: () {
                                      setState(() {
                                        _obscureConfirmPassword =
                                            !_obscureConfirmPassword;
                                      });
                                    },
                                    icon: Icon(
                                      _obscureConfirmPassword
                                          ? Icons.visibility_off_rounded
                                          : Icons.visibility_rounded,
                                      color: AppColors.textSecondary,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        )
                            .animate()
                            .fadeIn(delay: 120.ms, duration: 450.ms)
                            .slideY(begin: 0.1, end: 0, duration: 450.ms),
                        const SizedBox(height: 18),
                        GlassCard(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 18,
                            vertical: 16,
                          ),
                          borderRadius: 20,
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                height: 40,
                                width: 40,
                                decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(14),
                                  gradient: AppColors.primaryGradient,
                                ),
                                child: const Icon(
                                  Icons.shield_moon_outlined,
                                  color: AppColors.textPrimary,
                                  size: 20,
                                ),
                              ),
                              const SizedBox(width: 14),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      'Your data is secure with us.',
                                      style: textTheme.bodyMedium?.copyWith(
                                        color: AppColors.textPrimary,
                                        fontWeight: FontWeight.w700,
                                      ),
                                    ),
                                    const SizedBox(height: 6),
                                    Text(
                                      'We never share your information.',
                                      style: textTheme.bodyMedium,
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        )
                            .animate()
                            .fadeIn(delay: 210.ms, duration: 420.ms)
                            .slideY(begin: 0.08, end: 0, duration: 420.ms),
                        const SizedBox(height: 20),
                        AppButton(
                          label: 'Create Account',
                          icon: Icons.person_add_alt_1_rounded,
                          isLoading: _isLoading,
                          onPressed: _isLoading ? null : _handleRegister,
                        )
                            .animate()
                            .fadeIn(delay: 280.ms, duration: 420.ms)
                            .slideY(begin: 0.08, end: 0, duration: 420.ms),
                        const SizedBox(height: 18),
                        Center(
                          child: Wrap(
                            crossAxisAlignment: WrapCrossAlignment.center,
                            children: [
                              Text(
                                'Already have an account? ',
                                style: textTheme.bodyMedium,
                              ),
                              TextButton(
                                onPressed: () {
                                  Navigator.of(context).pushReplacementNamed(
                                    AppRoutes.login,
                                  );
                                },
                                child: const Text('Login'),
                              ),
                            ],
                          ),
                        ),
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

  String? Function(String?) _validateRequired(String message) {
    return (value) {
      if ((value?.trim() ?? '').isEmpty) {
        return message;
      }
      return null;
    };
  }

  String? _validateFullName(String? value) {
    final fullName = value?.trim() ?? '';
    if (fullName.isEmpty) {
      return 'Full name is required';
    }
    if (fullName.length < 3) {
      return 'Full name must be at least 3 characters';
    }
    if (RegExp(r'\d').hasMatch(fullName)) {
      return 'Full name cannot contain numbers';
    }
    return null;
  }

  String? _validateEmail(String? value) {
    final email = value?.trim() ?? '';
    if (email.isEmpty) {
      return 'Email is required';
    }

    final emailPattern = RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$');
    if (!emailPattern.hasMatch(email)) {
      return 'Enter a valid email address';
    }

    return null;
  }

  String? _validatePassword(String? value) {
    final password = value ?? '';
    if (password.isEmpty) {
      return 'Password is required';
    }
    if (password.length < 6) {
      return 'Password must be at least 6 characters';
    }
    if (!RegExp(r'[A-Za-z]').hasMatch(password) ||
        !RegExp(r'\d').hasMatch(password)) {
      return 'Password must contain at least one letter and one number';
    }
    return null;
  }

  String? _validatePhone(String? value) {
    final phone = value?.trim() ?? '';
    if (phone.isEmpty) {
      return 'Phone number is required';
    }

    final isValid = RegExp(
      r'^(?:01[0125]\d{8}|(?:\+20|0020)1[0125]\d{8})$',
    ).hasMatch(phone);

    if (!isValid) {
      return 'Enter a valid Egyptian mobile number';
    }
    return null;
  }

  String? _validateConfirmPassword(String? value) {
    final confirmPassword = value ?? '';
    if (confirmPassword.isEmpty) {
      return 'Please confirm your password';
    }
    if (confirmPassword != _passwordController.text) {
      return 'Passwords do not match';
    }
    return null;
  }
}

class _RegisterHero extends StatelessWidget {
  const _RegisterHero();

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Column(
      children: [
        SizedBox(
          width: 240,
          height: 150,
          child: Stack(
            alignment: Alignment.center,
            children: [
              Container(
                width: 136,
                height: 136,
                decoration: const BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: AppColors.heroGlowGradient,
                ),
              ),
              Container(
                width: 104,
                height: 104,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppColors.card.withValues(alpha: 0.8),
                  border: Border.all(
                    color: AppColors.primaryLight.withValues(alpha: 0.34),
                  ),
                ),
                child: const Icon(
                  Icons.school_rounded,
                  color: AppColors.textPrimary,
                  size: 44,
                ),
              ),
              const Positioned(
                left: 30,
                top: 48,
                child: GlowIconCard(icon: Icons.auto_awesome_rounded),
              ),
              const Positioned(
                right: 30,
                top: 18,
                child: GlowIconCard(icon: Icons.menu_book_rounded),
              ),
            ],
          ),
        ),
        Wrap(
          alignment: WrapAlignment.center,
          spacing: 2,
          children: [
            Text(
              'Grad',
              style: textTheme.displaySmall?.copyWith(
                fontSize: 30,
                fontWeight: FontWeight.w800,
                letterSpacing: -1.4,
              ),
            ),
            GradientText(
              text: 'Pilot',
              gradient: AppColors.primaryGradient,
              style: textTheme.displaySmall?.copyWith(
                fontSize: 30,
                fontWeight: FontWeight.w800,
                letterSpacing: -1.4,
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _RegisterBackground extends StatelessWidget {
  const _RegisterBackground();

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Stack(
        children: [
          Positioned(
            top: -30,
            left: -50,
            child: _GlowBlob(
              size: 170,
              color: AppColors.primary.withValues(alpha: 0.14),
            ),
          ),
          Positioned(
            right: -60,
            bottom: 140,
            child: _GlowBlob(
              size: 210,
              color: AppColors.secondary.withValues(alpha: 0.1),
            ),
          ),
          const Positioned(top: 150, right: 48, child: _Spark(size: 3)),
          const Positioned(bottom: 210, left: 40, child: _Spark(size: 5)),
          Positioned(
            top: 220,
            left: 42,
            child: _OutlineCircle(
              size: 58,
              color: AppColors.primaryLight.withValues(alpha: 0.14),
            ),
          ),
          Positioned(
            bottom: 120,
            right: 28,
            child: _OutlineCircle(
              size: 70,
              color: AppColors.secondary.withValues(alpha: 0.12),
            ),
          ),
        ],
      ),
    );
  }
}

class _GlowBlob extends StatelessWidget {
  const _GlowBlob({
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
            spreadRadius: 18,
          ),
        ],
      ),
    );
  }
}

class _Spark extends StatelessWidget {
  const _Spark({required this.size});

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

class _OutlineCircle extends StatelessWidget {
  const _OutlineCircle({
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
        border: Border.all(color: color),
      ),
    );
  }
}
