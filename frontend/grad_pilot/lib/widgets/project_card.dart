import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../models/generated_project.dart';
import 'glass_card.dart';

class ProjectCard extends StatelessWidget {
  const ProjectCard({
    super.key,
    required this.project,
    required this.onDetails,
    required this.onChat,
    this.onSave,
    this.onBlueprint,
    this.onEdit,
    this.onDelete,
    this.onFavorite,
    this.isSaving = false,
    this.isSaved = false,
    this.isFavorite = false,
  });

  final GeneratedProject project;
  final VoidCallback onDetails;
  final VoidCallback onChat;
  final VoidCallback? onSave;
  final VoidCallback? onBlueprint;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;
  final VoidCallback? onFavorite;
  final bool isSaving;
  final bool isSaved;
  final bool isFavorite;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final techStack = project.techStack.take(4).toList();
    final remainingTechCount =
        project.techStack.length > 4 ? project.techStack.length - 4 : 0;

    return GlassCard(
      padding: const EdgeInsets.all(18),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      project.title,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: textTheme.titleMedium?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w800,
                        fontSize: 19,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        _SourceStatusBadge(status: project.sourceStatus),
                        _MetaChip(label: project.difficulty),
                        _MetaChip(label: project.category),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 14),
              _ScoreCircle(
                value: _formatScore(project.feasibilityScore),
                label: 'Fit',
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            project.description,
            maxLines: 3,
            overflow: TextOverflow.ellipsis,
            style: textTheme.bodyMedium?.copyWith(
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [
              _ScorePill(
                label: 'Source',
                value: _formatScore(project.sourceQualityScore),
              ),
              _ScorePill(
                label: 'Duration',
                value: project.durationMonths == null
                    ? '--'
                    : '${project.durationMonths} mo',
              ),
            ],
          ),
          if (techStack.isNotEmpty) ...[
            const SizedBox(height: 14),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ...techStack.map((item) => _MetaChip(label: item, compact: true)),
                if (remainingTechCount > 0)
                  _MetaChip(label: '+$remainingTechCount', compact: true),
              ],
            ),
          ],
          const SizedBox(height: 14),
          Row(
            mainAxisAlignment: MainAxisAlignment.end,
            children: [
              _ActionIconButton(
                tooltip: 'Details',
                icon: Icons.info_outline_rounded,
                onTap: onDetails,
              ),
              const SizedBox(width: 10),
              if (onSave != null) ...[
                _ActionIconButton(
                  tooltip: isSaved ? 'Saved' : 'Save',
                  icon: isSaved
                      ? Icons.bookmark_rounded
                      : Icons.bookmark_border_rounded,
                  onTap: isSaving ? null : onSave,
                  isLoading: isSaving,
                  foregroundColor:
                      isSaved ? const Color(0xFF22C55E) : AppColors.secondary,
                  backgroundColor: isSaved
                      ? const Color(0x1A22C55E)
                      : AppColors.surface.withValues(alpha: 0.92),
                  borderColor: isSaved
                      ? const Color(0x5522C55E)
                      : AppColors.border.withValues(alpha: 0.9),
                ),
                const SizedBox(width: 10),
              ],
              if (onFavorite != null) ...[
                _ActionIconButton(
                  tooltip: isFavorite ? 'Favorite' : 'Add favorite',
                  icon: isFavorite
                      ? Icons.favorite_rounded
                      : Icons.favorite_border_rounded,
                  onTap: onFavorite,
                  foregroundColor:
                      isFavorite ? const Color(0xFFF472B6) : AppColors.accent,
                ),
                const SizedBox(width: 10),
              ],
              if (onBlueprint != null) ...[
                _ActionIconButton(
                  tooltip: 'Blueprint',
                  icon: Icons.account_tree_outlined,
                  onTap: onBlueprint,
                ),
                const SizedBox(width: 10),
              ],
              if (onEdit != null) ...[
                _ActionIconButton(
                  tooltip: 'Edit',
                  icon: Icons.edit_outlined,
                  onTap: onEdit,
                ),
                const SizedBox(width: 10),
              ],
              if (onDelete != null) ...[
                _ActionIconButton(
                  tooltip: 'Delete',
                  icon: Icons.delete_outline_rounded,
                  onTap: onDelete,
                  foregroundColor: const Color(0xFFF87171),
                ),
                const SizedBox(width: 10),
              ],
              _ActionIconButton(
                tooltip: 'Chat',
                icon: Icons.chat_bubble_outline_rounded,
                onTap: onChat,
                isFilled: true,
              ),
            ],
          ),
        ],
      ),
    );
  }

  String _formatScore(double? value) {
    if (value == null) {
      return '--';
    }
    return value.toStringAsFixed(1);
  }
}

class _ScoreCircle extends StatelessWidget {
  const _ScoreCircle({
    required this.value,
    required this.label,
  });

  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Container(
      height: 68,
      width: 68,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        gradient: AppColors.primaryGradient,
        boxShadow: const [
          BoxShadow(
            color: Color(0x226D5DFB),
            blurRadius: 22,
            spreadRadius: 2,
          ),
        ],
      ),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            value,
            style: textTheme.titleMedium?.copyWith(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w800,
              fontSize: 18,
            ),
          ),
          Text(
            label,
            style: textTheme.bodySmall?.copyWith(
              color: AppColors.textPrimary.withValues(alpha: 0.85),
              fontSize: 11,
            ),
          ),
        ],
      ),
    );
  }
}

class _MetaChip extends StatelessWidget {
  const _MetaChip({
    required this.label,
    this.compact = false,
  });

  final String label;
  final bool compact;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: compact ? 10 : 12,
        vertical: compact ? 6 : 8,
      ),
      decoration: BoxDecoration(
        color: AppColors.surface.withValues(alpha: 0.95),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: AppColors.border.withValues(alpha: 0.9)),
      ),
      child: Text(
        label,
        style: Theme.of(context).textTheme.bodySmall?.copyWith(
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w600,
            ),
      ),
    );
  }
}

class _SourceStatusBadge extends StatelessWidget {
  const _SourceStatusBadge({required this.status});

  final String status;

  @override
  Widget build(BuildContext context) {
    final normalized = status.toLowerCase();
    Color color;
    String label;
    IconData icon;

    switch (normalized) {
      case 'real_sources':
        color = const Color(0xFF22C55E);
        label = 'Verified';
        icon = Icons.verified_rounded;
        break;
      case 'paper_only':
        color = AppColors.secondary;
        label = 'Paper';
        icon = Icons.description_outlined;
        break;
      case 'repo_only':
        color = const Color(0xFFF59E0B);
        label = 'Repo';
        icon = Icons.code_rounded;
        break;
      default:
        color = AppColors.accent;
        label = 'Review';
        icon = Icons.help_outline_rounded;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.14),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 6),
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: color,
                  fontWeight: FontWeight.w700,
                ),
          ),
        ],
      ),
    );
  }
}

class _ScorePill extends StatelessWidget {
  const _ScorePill({
    required this.label,
    required this.value,
  });

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.surface.withValues(alpha: 0.82),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(color: AppColors.border.withValues(alpha: 0.9)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            value,
            style: textTheme.bodyMedium?.copyWith(
              color: AppColors.textPrimary,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(width: 8),
          Text(
            label,
            style: textTheme.bodySmall?.copyWith(color: AppColors.muted),
          ),
        ],
      ),
    );
  }
}

class _ActionIconButton extends StatelessWidget {
  const _ActionIconButton({
    required this.tooltip,
    required this.icon,
    required this.onTap,
    this.isLoading = false,
    this.isFilled = false,
    this.foregroundColor = AppColors.textPrimary,
    this.backgroundColor,
    this.borderColor,
  });

  final String tooltip;
  final IconData icon;
  final VoidCallback? onTap;
  final bool isLoading;
  final bool isFilled;
  final Color foregroundColor;
  final Color? backgroundColor;
  final Color? borderColor;

  @override
  Widget build(BuildContext context) {
    final bgColor = backgroundColor ??
        (isFilled
            ? AppColors.primary
            : AppColors.surface.withValues(alpha: 0.92));

    return Tooltip(
      message: tooltip,
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: isLoading ? null : onTap,
          borderRadius: BorderRadius.circular(999),
          child: Ink(
            height: 42,
            width: 42,
            decoration: BoxDecoration(
              color: bgColor,
              shape: BoxShape.circle,
              border: Border.all(
                color: borderColor ??
                    (isFilled
                        ? Colors.transparent
                        : AppColors.border.withValues(alpha: 0.9)),
              ),
            ),
            child: Center(
              child: isLoading
                  ? SizedBox(
                      height: 18,
                      width: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        valueColor: AlwaysStoppedAnimation<Color>(
                          foregroundColor,
                        ),
                      ),
                    )
                  : Icon(
                      icon,
                      size: 20,
                      color: isFilled ? AppColors.textPrimary : foregroundColor,
                    ),
            ),
          ),
        ),
      ),
    );
  }
}
