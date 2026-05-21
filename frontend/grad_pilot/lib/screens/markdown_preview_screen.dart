import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../core/app_colors.dart';
import '../core/app_config.dart';
import '../widgets/app_button.dart';
import '../widgets/glass_card.dart';

class MarkdownPreviewScreen extends StatelessWidget {
  const MarkdownPreviewScreen({
    super.key,
    required this.markdown,
  });

  final String markdown;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Markdown Preview'),
        backgroundColor: Colors.transparent,
      ),
      body: Container(
        decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
        child: SafeArea(
          top: false,
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: AppConfig.contentMaxWidth),
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    AppButton(
                      label: 'Copy Markdown',
                      icon: Icons.copy_rounded,
                      onPressed: () async {
                        await Clipboard.setData(ClipboardData(text: markdown));
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            const SnackBar(content: Text('Markdown copied.')),
                          );
                        }
                      },
                    ),
                    const SizedBox(height: 16),
                    Expanded(
                      child: GlassCard(
                        padding: const EdgeInsets.all(0),
                        child: SingleChildScrollView(
                          padding: const EdgeInsets.all(18),
                          child: SelectableText(
                            markdown.trim().isEmpty
                                ? 'No markdown content returned.'
                                : markdown,
                            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                                  color: AppColors.textSecondary,
                                  fontFamily: 'monospace',
                                ),
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
