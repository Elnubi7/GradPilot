import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../core/app_colors.dart';
import '../core/app_config.dart';
import '../models/generated_projects_response.dart';
import '../services/api_service.dart';
import '../widgets/app_button.dart';
import '../widgets/app_text_field.dart';
import '../widgets/glass_card.dart';
import '../widgets/loading_view.dart';
import 'generated_projects_screen.dart';

class GenerateIdeasScreen extends StatefulWidget {
  const GenerateIdeasScreen({super.key});

  @override
  State<GenerateIdeasScreen> createState() => _GenerateIdeasScreenState();
}

class _GenerateIdeasScreenState extends State<GenerateIdeasScreen> {
  final _apiService = const ApiService();
  final _promptController = TextEditingController();

  int _maxResults = 5;
  bool _isLoading = false;
  String? _errorMessage;

  static const _quickPrompts = [
    'AI',
    'Healthcare',
    'Education',
    'Flutter',
    'FastAPI',
    'Python',
    '5 months',
    '3 members',
  ];

  @override
  void dispose() {
    _promptController.dispose();
    super.dispose();
  }

  Future<void> _handleGenerate() async {
    final prompt = _promptController.text.trim();
    if (prompt.length < 10) {
      setState(() {
        _errorMessage = 'Please enter at least 10 characters describing your idea.';
      });
      return;
    }

    setState(() {
      _errorMessage = null;
      _isLoading = true;
    });

    try {
      final GeneratedProjectsResponse response =
          await _apiService.generateProjects(
        promptText: prompt,
        maxResults: _maxResults,
      );

      if (!mounted) {
        return;
      }

      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => GeneratedProjectsScreen(response: response),
        ),
      );
    } catch (error) {
      if (!mounted) {
        return;
      }

      final message = error.toString();
      setState(() {
        _errorMessage = message;
      });
      if (!_isRateLimitMessage(message)) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(message)),
        );
      }
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _appendPrompt(String value) {
    final current = _promptController.text.trim();
    final next = current.isEmpty ? value : '$current, $value';
    _promptController.value = TextEditingValue(
      text: next,
      selection: TextSelection.collapsed(offset: next.length),
    );
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Generate Ideas'),
        backgroundColor: Colors.transparent,
      ),
      body: Container(
        decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
        child: SafeArea(
          top: false,
          child: AnimatedSwitcher(
            duration: const Duration(milliseconds: 220),
            child: _isLoading
                ? const Padding(
                    key: ValueKey('loading'),
                    padding: EdgeInsets.all(24),
                    child: LoadingView(
                      title: 'Generating Verified Ideas',
                      lines: [
                        'Searching GitHub and arXiv...',
                        'Generating source-backed ideas...',
                      ],
                    ),
                  )
                : SingleChildScrollView(
                    key: const ValueKey('form'),
                    padding: const EdgeInsets.all(24),
                    child: Center(
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(
                          maxWidth: AppConfig.contentMaxWidth,
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Tell GradPilot what you want',
                              style: textTheme.headlineMedium?.copyWith(
                                fontWeight: FontWeight.w800,
                                fontSize: 30,
                              ),
                            )
                                .animate()
                                .fadeIn(duration: 420.ms)
                                .slideY(
                                  begin: 0.08,
                                  end: 0,
                                  duration: 420.ms,
                                ),
                            const SizedBox(height: 8),
                            Text(
                              'Example: "احنا 3 في التيم وعايزين AI healthcare mobile app باستخدام Flutter و FastAPI و Python ويتعمل في 5 شهور"',
                              style: textTheme.bodyLarge,
                            ).animate(delay: 80.ms).fadeIn(duration: 380.ms),
                            const SizedBox(height: 22),
                            GlassCard(
                              padding: const EdgeInsets.all(22),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  AppTextField(
                                    label: 'Project Prompt',
                                    hint:
                                        'Describe your team, domain, stack, and timeline...',
                                    controller: _promptController,
                                    prefixIcon: Icons.edit_note_rounded,
                                    keyboardType: TextInputType.multiline,
                                    textInputAction: TextInputAction.newline,
                                    maxLines: 8,
                                    minLines: 6,
                                  ),
                                  const SizedBox(height: 18),
                                  Text(
                                    'Quick Add',
                                    style: textTheme.bodyMedium?.copyWith(
                                      color: AppColors.textPrimary,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                  const SizedBox(height: 12),
                                  Wrap(
                                    spacing: 10,
                                    runSpacing: 10,
                                    children: _quickPrompts
                                        .map(
                                          (item) => ActionChip(
                                            onPressed: () => _appendPrompt(item),
                                            backgroundColor: AppColors.surface,
                                            side: BorderSide(
                                              color: AppColors.border.withValues(
                                                alpha: 0.9,
                                              ),
                                            ),
                                            label: Text(
                                              item,
                                              style: textTheme.bodySmall?.copyWith(
                                                color: AppColors.textSecondary,
                                                fontWeight: FontWeight.w600,
                                              ),
                                            ),
                                          ),
                                        )
                                        .toList(),
                                  ),
                                  const SizedBox(height: 18),
                                  Text(
                                    'Max Results',
                                    style: textTheme.bodyMedium?.copyWith(
                                      color: AppColors.textPrimary,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                  const SizedBox(height: 12),
                                  Wrap(
                                    spacing: 10,
                                    children: [3, 5, 8]
                                        .map(
                                          (value) => ChoiceChip(
                                            label: Text(value.toString()),
                                            selected: _maxResults == value,
                                            onSelected: (_) {
                                              setState(() {
                                                _maxResults = value;
                                              });
                                            },
                                          ),
                                        )
                                        .toList(),
                                  ),
                                  if (_errorMessage != null) ...[
                                    const SizedBox(height: 18),
                                    Container(
                                      width: double.infinity,
                                      padding: const EdgeInsets.all(14),
                                      decoration: BoxDecoration(
                                        color: const Color(0x33EF4444),
                                        borderRadius: BorderRadius.circular(18),
                                        border: Border.all(
                                          color: const Color(0x55EF4444),
                                        ),
                                      ),
                                      child: Text(
                                        _errorMessage!,
                                        style: textTheme.bodyMedium?.copyWith(
                                          color: AppColors.textPrimary,
                                        ),
                                      ),
                                    ),
                                  ],
                                  const SizedBox(height: 20),
                                  AppButton(
                                    label: 'Generate Verified Ideas',
                                    icon: Icons.auto_awesome_rounded,
                                    onPressed: _handleGenerate,
                                  ),
                                ],
                              ),
                            )
                                .animate(delay: 140.ms)
                                .fadeIn(duration: 420.ms)
                                .slideY(begin: 0.08, end: 0, duration: 420.ms),
                          ],
                        ),
                      ),
                    ),
                  ),
          ),
        ),
      ),
    );
  }

  bool _isRateLimitMessage(String message) {
    final normalized = message.toLowerCase();
    return normalized.contains('arxiv rate limited') ||
        normalized.contains('rate limited') ||
        normalized.contains('try again later');
  }
}
