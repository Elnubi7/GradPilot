import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../core/app_colors.dart';
import '../core/app_config.dart';
import '../core/app_routes.dart';
import '../data/local_user_store.dart';
import '../models/auth_response.dart';
import '../services/api_service.dart';
import '../widgets/app_button.dart';
import '../widgets/app_text_field.dart';
import '../widgets/glass_card.dart';
import '../widgets/glow_icon_card.dart';
import '../widgets/gradient_text.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _userStore = const LocalUserStore();
  final _apiService = const ApiService();

  bool _obscurePassword = true;
  bool _rememberMe = true;
  bool _isLoading = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    try {
      final AuthResponse response = await _apiService.login(
        email: _emailController.text,
        password: _passwordController.text,
      );

      if (!mounted) {
        return;
      }

      if (!response.success || response.user == null) {
        _showMessage(response.message.isEmpty
            ? 'Invalid email or password'
            : response.message);
        return;
      }

      await _userStore.saveCurrentUser(response.user!);
      if (!mounted) {
        return;
      }
      Navigator.of(context).pushNamedAndRemoveUntil(
        AppRoutes.main,
        (route) => false,
      );
    } on ApiException catch (error) {
      final message = error.message;
      if (_isBackendOffline(message)) {
        final fallbackUser = await _userStore.login(
          _emailController.text,
          _passwordController.text,
        );

        if (fallbackUser != null &&
            _emailController.text.trim().toLowerCase() ==
                'student@gradpilot.app') {
          await _userStore.saveCurrentUser(fallbackUser);
          if (!mounted) {
            return;
          }
          Navigator.of(context).pushNamedAndRemoveUntil(
            AppRoutes.main,
            (route) => false,
          );
          return;
        }
      }

      if (!mounted) {
        return;
      }
      _showMessage(message);
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
            const _AuthBackground(),
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
                        const SizedBox(height: 20),
                        const _AuthHero()
                            .animate()
                            .fadeIn(duration: 500.ms)
                            .slideY(begin: 0.08, end: 0, duration: 500.ms)
                            .scale(
                              begin: const Offset(0.97, 0.97),
                              end: const Offset(1, 1),
                              duration: 500.ms,
                            ),
                        const SizedBox(height: 26),
                        Text(
                          'Welcome Back',
                          style: textTheme.headlineMedium?.copyWith(
                            fontSize: 30,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Login to continue your journey',
                          style: textTheme.bodyLarge,
                        ),
                        const SizedBox(height: 24),
                        GlassCard(
                          padding: const EdgeInsets.all(22),
                          child: Form(
                            key: _formKey,
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                AppTextField(
                                  label: 'Email Address',
                                  hint: 'student@gradpilot.app',
                                  controller: _emailController,
                                  prefixIcon: Icons.alternate_email_rounded,
                                  keyboardType: TextInputType.emailAddress,
                                  textInputAction: TextInputAction.next,
                                  validator: _validateEmail,
                                ),
                                const SizedBox(height: 18),
                                AppTextField(
                                  label: 'Password',
                                  hint: 'Enter your password',
                                  controller: _passwordController,
                                  prefixIcon: Icons.lock_outline_rounded,
                                  obscureText: _obscurePassword,
                                  textInputAction: TextInputAction.done,
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
                                const SizedBox(height: 16),
                                Row(
                                  children: [
                                    InkWell(
                                      onTap: () {
                                        setState(() {
                                          _rememberMe = !_rememberMe;
                                        });
                                      },
                                      borderRadius: BorderRadius.circular(8),
                                      child: Row(
                                        children: [
                                          Container(
                                            height: 18,
                                            width: 18,
                                            decoration: BoxDecoration(
                                              borderRadius:
                                                  BorderRadius.circular(5),
                                              gradient: _rememberMe
                                                  ? AppColors.primaryGradient
                                                  : null,
                                              color: _rememberMe
                                                  ? null
                                                  : AppColors.surface,
                                              border: Border.all(
                                                color: _rememberMe
                                                    ? Colors.transparent
                                                    : AppColors.border,
                                              ),
                                            ),
                                            child: _rememberMe
                                                ? const Icon(
                                                    Icons.check_rounded,
                                                    size: 14,
                                                    color:
                                                        AppColors.textPrimary,
                                                  )
                                                : null,
                                          ),
                                          const SizedBox(width: 10),
                                          Text(
                                            'Remember me',
                                            style: textTheme.bodyMedium,
                                          ),
                                        ],
                                      ),
                                    ),
                                    const Spacer(),
                                    Text(
                                      'Forgot password?',
                                      style: textTheme.bodyMedium?.copyWith(
                                        color: AppColors.secondary,
                                        fontWeight: FontWeight.w600,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 22),
                                AppButton(
                                  label: 'Login',
                                  icon: Icons.arrow_forward_rounded,
                                  isLoading: _isLoading,
                                  onPressed: _isLoading ? null : _handleLogin,
                                ),
                              ],
                            ),
                          ),
                        )
                            .animate()
                            .fadeIn(delay: 120.ms, duration: 450.ms)
                            .slideY(begin: 0.1, end: 0, duration: 450.ms),
                        const SizedBox(height: 22),
                        Row(
                          children: [
                            Expanded(
                              child: Container(
                                height: 1,
                                color: AppColors.border.withValues(alpha: 0.8),
                              ),
                            ),
                            Padding(
                              padding:
                                  const EdgeInsets.symmetric(horizontal: 14),
                              child: Text(
                                'or continue with',
                                style: textTheme.bodyMedium?.copyWith(
                                  color: AppColors.muted,
                                ),
                              ),
                            ),
                            Expanded(
                              child: Container(
                                height: 1,
                                color: AppColors.border.withValues(alpha: 0.8),
                              ),
                            ),
                          ],
                        )
                            .animate()
                            .fadeIn(delay: 220.ms, duration: 380.ms),
                        const SizedBox(height: 18),
                        Row(
                          children: const [
                            Expanded(
                              child: _SocialButton(
                                icon: Icons.public_rounded,
                                label: 'Google',
                              ),
                            ),
                            SizedBox(width: 12),
                            Expanded(
                              child: _SocialButton(
                                icon: Icons.code_rounded,
                                label: 'GitHub',
                              ),
                            ),
                          ],
                        )
                            .animate()
                            .fadeIn(delay: 260.ms, duration: 400.ms)
                            .slideY(begin: 0.08, end: 0, duration: 400.ms),
                        const SizedBox(height: 22),
                        Center(
                          child: Wrap(
                            crossAxisAlignment: WrapCrossAlignment.center,
                            children: [
                              Text(
                                'Don\'t have an account? ',
                                style: textTheme.bodyMedium,
                              ),
                              TextButton(
                                onPressed: () {
                                  Navigator.of(context).pushNamed(
                                    AppRoutes.register,
                                  );
                                },
                                child: const Text('Sign up'),
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
    return null;
  }

  bool _isBackendOffline(String message) {
    return message.toLowerCase().contains('backend is not running');
  }

  void _showMessage(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }
}

class _AuthHero extends StatelessWidget {
  const _AuthHero();

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Column(
      children: [
        SizedBox(
          width: 270,
          height: 190,
          child: Stack(
            alignment: Alignment.center,
            clipBehavior: Clip.none,
            children: [
              Container(
                width: 180,
                height: 180,
                decoration: const BoxDecoration(
                  shape: BoxShape.circle,
                  gradient: AppColors.heroGlowGradient,
                ),
              ),
              Container(
                width: 136,
                height: 136,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  color: AppColors.card.withValues(alpha: 0.75),
                  border: Border.all(
                    color: AppColors.primaryLight.withValues(alpha: 0.32),
                  ),
                  boxShadow: const [
                    BoxShadow(
                      color: Color(0x226D5DFB),
                      blurRadius: 28,
                      spreadRadius: 8,
                    ),
                  ],
                ),
                child: const Icon(
                  Icons.smart_toy_rounded,
                  color: AppColors.textPrimary,
                  size: 56,
                ),
              ),
              const Positioned(
                left: 28,
                top: 74,
                child: GlowIconCard(icon: Icons.school_rounded),
              ),
              const Positioned(
                right: 26,
                top: 26,
                child: GlowIconCard(icon: Icons.auto_awesome_rounded),
              ),
              const Positioned(
                right: 44,
                bottom: 10,
                child: GlowIconCard(icon: Icons.psychology_alt_rounded),
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
                fontSize: 34,
                fontWeight: FontWeight.w800,
                letterSpacing: -1.6,
              ),
            ),
            GradientText(
              text: 'Pilot',
              gradient: AppColors.primaryGradient,
              style: textTheme.displaySmall?.copyWith(
                fontSize: 34,
                fontWeight: FontWeight.w800,
                letterSpacing: -1.6,
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        Text(
          AppConfig.subtitle,
          textAlign: TextAlign.center,
          style: textTheme.bodyLarge?.copyWith(
            color: AppColors.textSecondary,
          ),
        ),
      ],
    );
  }
}

class _SocialButton extends StatelessWidget {
  const _SocialButton({
    required this.icon,
    required this.label,
  });

  final IconData icon;
  final String label;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return GlassCard(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 14),
      borderRadius: 18,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, color: AppColors.textPrimary, size: 20),
          const SizedBox(width: 10),
          Text(
            label,
            style: textTheme.bodyMedium?.copyWith(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }
}

class _AuthBackground extends StatelessWidget {
  const _AuthBackground();

  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: Stack(
        children: [
          Positioned(
            top: -50,
            right: -40,
            child: _BlurOrb(
              size: 170,
              color: AppColors.primary.withValues(alpha: 0.16),
            ),
          ),
          Positioned(
            bottom: 120,
            left: -70,
            child: _BlurOrb(
              size: 210,
              color: AppColors.secondary.withValues(alpha: 0.1),
            ),
          ),
          const Positioned(top: 120, left: 42, child: _Dot(size: 4)),
          const Positioned(top: 200, right: 60, child: _Dot(size: 3)),
          const Positioned(bottom: 180, left: 60, child: _Dot(size: 5)),
          Positioned(
            top: 160,
            right: 40,
            child: _Ring(
              size: 52,
              color: AppColors.primaryLight.withValues(alpha: 0.14),
            ),
          ),
          Positioned(
            bottom: 120,
            right: 32,
            child: _Ring(
              size: 68,
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
            spreadRadius: 20,
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
        border: Border.all(color: color),
      ),
    );
  }
}
