import 'package:flutter/material.dart';

import '../core/app_colors.dart';

class ChatBubble extends StatelessWidget {
  const ChatBubble({
    super.key,
    required this.text,
    required this.isUser,
    this.isLoading = false,
  });

  final String text;
  final bool isUser;
  final bool isLoading;

  @override
  Widget build(BuildContext context) {
    final alignment = isUser ? Alignment.centerRight : Alignment.centerLeft;
    final color = isUser
        ? AppColors.primary.withValues(alpha: 0.95)
        : AppColors.card.withValues(alpha: 0.82);
    final borderColor = isUser
        ? AppColors.primaryLight.withValues(alpha: 0.28)
        : AppColors.border.withValues(alpha: 0.95);

    return Align(
      alignment: alignment,
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 560),
        child: Container(
          margin: const EdgeInsets.only(bottom: 12),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.only(
              topLeft: const Radius.circular(18),
              topRight: const Radius.circular(18),
              bottomLeft: Radius.circular(isUser ? 18 : 6),
              bottomRight: Radius.circular(isUser ? 6 : 18),
            ),
            border: Border.all(color: borderColor),
          ),
          child: isLoading
              ? const SizedBox(
                  width: 44,
                  child: LinearProgressIndicator(minHeight: 3),
                )
              : Text(
                  text,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textPrimary,
                      ),
                ),
        ),
      ),
    );
  }
}
