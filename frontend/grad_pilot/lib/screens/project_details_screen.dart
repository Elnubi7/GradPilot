import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_config.dart';
import '../models/generated_project.dart';
import '../services/api_service.dart';
import '../widgets/app_button.dart';
import '../widgets/glass_card.dart';
import '../widgets/score_pill.dart';
import '../widgets/section_card.dart';
import '../widgets/source_link_button.dart';
import 'blueprint_screen.dart';
import 'project_chat_screen.dart';

class ProjectDetailsScreen extends StatefulWidget {
  const ProjectDetailsScreen({
    super.key,
    required this.project,
  });

  final GeneratedProject project;

  @override
  State<ProjectDetailsScreen> createState() => _ProjectDetailsScreenState();
}

class _ProjectDetailsScreenState extends State<ProjectDetailsScreen> {
  final _apiService = const ApiService();

  bool _isSaving = false;
  bool _isSaved = false;

  @override
  Widget build(BuildContext context) {
    final project = widget.project;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Project Details'),
        backgroundColor: Colors.transparent,
      ),
      body: Container(
        decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
        child: SafeArea(
          top: false,
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(
                maxWidth: AppConfig.contentMaxWidth,
              ),
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(24),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _HeaderCard(project: project),
                    const SizedBox(height: 16),
                    Wrap(
                      spacing: 10,
                      runSpacing: 10,
                      children: [
                        ScorePill(
                          label: 'Feasibility',
                          value: project.feasibilityScore,
                        ),
                        ScorePill(
                          label: 'Source Quality',
                          value: project.sourceQualityScore,
                        ),
                        ScorePill(label: 'Paper', value: project.paperScore),
                        ScorePill(
                          label: 'Repo',
                          value: project.repositoryScore,
                        ),
                      ],
                    ),
                    const SizedBox(height: 16),
                    _TextSection(title: 'Problem', value: project.problem),
                    _TextSection(title: 'Solution', value: project.solution),
                    _ListSection(title: 'Features', values: project.features),
                    _ListSection(
                      title: 'Evaluation Metrics',
                      values: project.evaluationMetrics,
                    ),
                    _ListSection(title: 'Tech Stack', values: project.techStack),
                    _ListSection(
                      title: 'Weekly Milestones',
                      values: project.weeklyMilestones,
                    ),
                    _ListSection(title: 'Risks', values: project.risks),
                    _ListSection(
                      title: 'Source Titles',
                      values: project.sourceTitles,
                    ),
                    _SourceLinks(project: project),
                    const SizedBox(height: 18),
                    _ActionButtons(
                      isSaving: _isSaving,
                      isSaved: _isSaved,
                      onSave: _handleSave,
                      onChat: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => ProjectChatScreen(project: project),
                          ),
                        );
                      },
                      onBlueprint: () {
                        Navigator.of(context).push(
                          MaterialPageRoute(
                            builder: (_) => BlueprintScreen(project: project),
                          ),
                        );
                      },
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

  Future<void> _handleSave() async {
    setState(() {
      _isSaving = true;
    });

    try {
      final message = await _apiService.saveGeneratedProject(widget.project);
      if (!mounted) {
        return;
      }
      setState(() {
        _isSaved = true;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(message.isEmpty ? 'Project saved' : message)),
      );
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      final lower = error.message.toLowerCase();
      if (lower.contains('already') ||
          lower.contains('duplicate') ||
          lower.contains('exists')) {
        setState(() {
          _isSaved = true;
        });
      }
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text(error.message)),
      );
    } finally {
      if (mounted) {
        setState(() {
          _isSaving = false;
        });
      }
    }
  }
}

class _HeaderCard extends StatelessWidget {
  const _HeaderCard({required this.project});

  final GeneratedProject project;

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;

    return GlassCard(
      padding: const EdgeInsets.all(22),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            project.title,
            style: textTheme.headlineMedium?.copyWith(
              fontWeight: FontWeight.w800,
              fontSize: 28,
            ),
          ),
          const SizedBox(height: 14),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _Chip(label: project.category, color: AppColors.secondary),
              _Chip(label: project.difficulty, color: AppColors.accent),
              _Chip(
                label: _sourceStatusLabel(project.sourceStatus),
                color: _sourceStatusColor(project.sourceStatus),
                icon: Icons.verified_outlined,
              ),
            ],
          ),
          const SizedBox(height: 14),
          Text(
            project.description,
            style: textTheme.bodyLarge,
          ),
        ],
      ),
    );
  }
}

class _Chip extends StatelessWidget {
  const _Chip({
    required this.label,
    required this.color,
    this.icon,
  });

  final String label;
  final Color color;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
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
          if (icon != null) ...[
            Icon(icon, size: 14, color: color),
            const SizedBox(width: 6),
          ],
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: color,
                  fontWeight: FontWeight.w800,
                ),
          ),
        ],
      ),
    );
  }
}

class _TextSection extends StatelessWidget {
  const _TextSection({
    required this.title,
    required this.value,
  });

  final String title;
  final String value;

  @override
  Widget build(BuildContext context) {
    final text = value.trim();
    return Padding(
      padding: const EdgeInsets.only(top: 14),
      child: SectionCard(
        title: title,
        child: Text(
          text.isEmpty ? 'Not provided yet.' : text,
          style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: text.isEmpty ? AppColors.muted : AppColors.textSecondary,
              ),
        ),
      ),
    );
  }
}

class _ListSection extends StatelessWidget {
  const _ListSection({
    required this.title,
    required this.values,
  });

  final String title;
  final List<String> values;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(top: 14),
      child: SectionCard(
        title: title,
        child: BulletList(items: values),
      ),
    );
  }
}

class _SourceLinks extends StatelessWidget {
  const _SourceLinks({required this.project});

  final GeneratedProject project;

  @override
  Widget build(BuildContext context) {
    final links = [
      if (project.paperLink.trim().isNotEmpty)
        SourceLinkButton(
          label: 'Open arXiv Paper',
          url: project.paperLink,
          icon: Icons.description_outlined,
        ),
      if (project.githubLink.trim().isNotEmpty)
        SourceLinkButton(
          label: 'Open GitHub Repo',
          url: project.githubLink,
          icon: Icons.code_rounded,
        ),
    ];

    if (links.isEmpty) {
      return const SizedBox.shrink();
    }

    return Padding(
      padding: const EdgeInsets.only(top: 14),
      child: SectionCard(
        title: 'Source Links',
        child: Wrap(
          spacing: 10,
          runSpacing: 10,
          children: links,
        ),
      ),
    );
  }
}

class _ActionButtons extends StatelessWidget {
  const _ActionButtons({
    required this.isSaving,
    required this.isSaved,
    required this.onSave,
    required this.onChat,
    required this.onBlueprint,
  });

  final bool isSaving;
  final bool isSaved;
  final VoidCallback onSave;
  final VoidCallback onChat;
  final VoidCallback onBlueprint;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final isWide = constraints.maxWidth > 520;
        final buttons = [
          AppButton(
            label: isSaved ? 'Saved Project' : 'Save Project',
            icon: isSaved ? Icons.bookmark_rounded : Icons.bookmark_add_outlined,
            isLoading: isSaving,
            onPressed: isSaved ? null : onSave,
            fullWidth: !isWide,
          ),
          AppButton(
            label: 'Chat with AI',
            icon: Icons.chat_bubble_outline_rounded,
            onPressed: onChat,
            fullWidth: !isWide,
          ),
          AppButton(
            label: 'View Blueprint',
            icon: Icons.account_tree_outlined,
            onPressed: onBlueprint,
            fullWidth: !isWide,
          ),
        ];

        if (!isWide) {
          return Column(
            children: [
              for (var index = 0; index < buttons.length; index++) ...[
                buttons[index],
                if (index != buttons.length - 1) const SizedBox(height: 12),
              ],
            ],
          );
        }

        return Wrap(
          spacing: 12,
          runSpacing: 12,
          children: buttons,
        );
      },
    );
  }
}

String _sourceStatusLabel(String status) {
  switch (status.toLowerCase()) {
    case 'real_sources':
      return 'Verified Sources';
    case 'paper_only':
      return 'Paper Only';
    case 'repo_only':
      return 'Repo Only';
    default:
      return 'Source Review';
  }
}

Color _sourceStatusColor(String status) {
  switch (status.toLowerCase()) {
    case 'real_sources':
      return const Color(0xFF22C55E);
    case 'paper_only':
      return AppColors.secondary;
    case 'repo_only':
      return const Color(0xFFF59E0B);
    default:
      return AppColors.accent;
  }
}
