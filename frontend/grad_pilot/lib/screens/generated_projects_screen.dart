import 'package:flutter/material.dart';
import 'package:flutter_animate/flutter_animate.dart';

import '../core/app_colors.dart';
import '../core/app_config.dart';
import '../models/generated_projects_response.dart';
import '../models/generated_project.dart';
import '../services/api_service.dart';
import '../widgets/empty_state.dart';
import '../widgets/glass_card.dart';
import '../widgets/project_card.dart';
import 'project_chat_screen.dart';
import 'project_details_screen.dart';

class GeneratedProjectsScreen extends StatefulWidget {
  const GeneratedProjectsScreen({
    super.key,
    required this.response,
  });

  final GeneratedProjectsResponse response;

  @override
  State<GeneratedProjectsScreen> createState() => _GeneratedProjectsScreenState();
}

class _GeneratedProjectsScreenState extends State<GeneratedProjectsScreen> {
  final _apiService = const ApiService();
  final Set<String> _savingProjectIds = <String>{};
  final Set<String> _savedProjectIds = <String>{};
  _ProjectFilter _selectedFilter = _ProjectFilter.all;

  List<GeneratedProject> get _filteredProjects {
    final projects = widget.response.generatedProjects;
    switch (_selectedFilter) {
      case _ProjectFilter.all:
        return projects;
      case _ProjectFilter.verified:
        return projects
            .where((project) => project.sourceStatus == 'real_sources')
            .toList();
      case _ProjectFilter.paperOnly:
        return projects
            .where((project) => project.sourceStatus == 'paper_only')
            .toList();
      case _ProjectFilter.repoOnly:
        return projects
            .where((project) => project.sourceStatus == 'repo_only')
            .toList();
    }
  }

  @override
  Widget build(BuildContext context) {
    final textTheme = Theme.of(context).textTheme;
    final response = widget.response;
    final projects = _filteredProjects;
    final hasRateLimitWarning = response.hasRateLimitWarning;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Generated Projects'),
        backgroundColor: Colors.transparent,
      ),
      body: Container(
        decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
        child: SafeArea(
          top: false,
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: AppConfig.contentMaxWidth),
              child: ListView.separated(
                padding: const EdgeInsets.all(24),
                itemBuilder: (context, index) {
                  if (index == 0) {
                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        GlassCard(
                          padding: const EdgeInsets.all(20),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text(
                                'Results Overview',
                                style: textTheme.titleMedium?.copyWith(
                                  color: AppColors.textPrimary,
                                  fontWeight: FontWeight.w800,
                                ),
                              ),
                              const SizedBox(height: 8),
                              Text(
                                response.message,
                                style: textTheme.bodyMedium?.copyWith(
                                  color: AppColors.textSecondary,
                                ),
                              ),
                              const SizedBox(height: 16),
                              _ResultStats(response: response),
                            ],
                          ),
                        )
                            .animate()
                            .fadeIn(duration: 420.ms)
                            .slideY(begin: 0.08, end: 0, duration: 420.ms),
                        if (hasRateLimitWarning && response.generatedProjects.isNotEmpty)
                          Padding(
                            padding: const EdgeInsets.only(top: 14),
                            child: const _WarningBanner(),
                          ),
                        const SizedBox(height: 18),
                        Wrap(
                          spacing: 10,
                          runSpacing: 10,
                          children: _ProjectFilter.values.map((filter) {
                            return ChoiceChip(
                              label: Text(filter.label),
                              selected: _selectedFilter == filter,
                              onSelected: (_) {
                                setState(() {
                                  _selectedFilter = filter;
                                });
                              },
                            );
                          }).toList(),
                        ),
                        if (projects.isEmpty) ...[
                          const SizedBox(height: 22),
                          _buildEmptyState(response),
                        ] else ...[
                          const SizedBox(height: 18),
                          ProjectCard(
                            project: projects[index],
                            isSaving: _savingProjectIds.contains(projects[index].id),
                            isSaved: _savedProjectIds.contains(projects[index].id),
                            onDetails: () => _openDetails(projects[index]),
                            onSave: () => _handleSave(projects[index]),
                            onChat: () => _openChat(projects[index]),
                          ),
                        ],
                      ],
                    );
                  }

                  final project = projects[index];
                  return ProjectCard(
                    project: project,
                    isSaving: _savingProjectIds.contains(project.id),
                    isSaved: _savedProjectIds.contains(project.id),
                    onDetails: () => _openDetails(project),
                    onSave: () => _handleSave(project),
                    onChat: () => _openChat(project),
                  );
                },
                separatorBuilder: (_, _) => const SizedBox(height: 16),
                itemCount: projects.isEmpty ? 1 : projects.length,
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState(GeneratedProjectsResponse response) {
    if (response.generatedProjects.isEmpty && response.hasRateLimitWarning) {
      return const EmptyState(
        title: 'Sources are temporarily limited',
        message: 'arXiv is rate limited. Try again later or use broader keywords.',
        icon: Icons.hourglass_top_rounded,
      );
    }

    if (response.generatedProjects.isEmpty) {
      return const EmptyState(
        title: 'No strong source-backed projects found.',
        message: 'Try broader keywords.',
        icon: Icons.search_off_rounded,
      );
    }

    return const EmptyState(
      title: 'No projects match this filter.',
      message: 'Try another source filter to see more ideas.',
      icon: Icons.filter_alt_off_rounded,
    );
  }

  Future<void> _handleSave(GeneratedProject project) async {
    setState(() {
      _savingProjectIds.add(project.id);
    });

    try {
      final message = await _apiService.saveGeneratedProject(project);
      final normalizedMessage = message.toLowerCase();
      final alreadySaved = normalizedMessage.contains('already') ||
          normalizedMessage.contains('duplicate') ||
          normalizedMessage.contains('exists');

      if (!mounted) {
        return;
      }

      setState(() {
        _savedProjectIds.add(project.id);
      });

      _showActionToast(
        context,
        alreadySaved
            ? message
            : (message.isEmpty ? 'Project saved successfully' : message),
      );
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      final message = error.message;
      final normalizedMessage = message.toLowerCase();
      final alreadySaved = normalizedMessage.contains('already') ||
          normalizedMessage.contains('duplicate') ||
          normalizedMessage.contains('exists');

      if (alreadySaved) {
        setState(() {
          _savedProjectIds.add(project.id);
        });
      }

      if (message.toLowerCase().contains('backend is not running')) {
        _showActionToast(context, 'Backend is not running.');
      } else {
        _showActionToast(context, message);
      }
    } finally {
      if (mounted) {
        setState(() {
          _savingProjectIds.remove(project.id);
        });
      }
    }
  }

  void _showActionToast(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
    );
  }

  void _openDetails(GeneratedProject project) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ProjectDetailsScreen(project: project),
      ),
    );
  }

  void _openChat(GeneratedProject project) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ProjectChatScreen(project: project),
      ),
    );
  }
}

enum _ProjectFilter {
  all('All'),
  verified('Verified'),
  paperOnly('Paper Only'),
  repoOnly('Repo Only');

  const _ProjectFilter(this.label);

  final String label;
}

class _ResultStats extends StatelessWidget {
  const _ResultStats({required this.response});

  final GeneratedProjectsResponse response;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: [
        _SummaryChip(
          label: 'Results',
          value: response.generatedProjects.length.toString(),
        ),
        _SummaryChip(
          label: 'Papers',
          value: response.papersFound.toString(),
        ),
        _SummaryChip(
          label: 'Repos',
          value: response.repositoriesFound.toString(),
        ),
      ],
    );
  }
}

class _WarningBanner extends StatelessWidget {
  const _WarningBanner();

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: const Color(0x33F59E0B),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0x55F59E0B)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.warning_amber_rounded,
            color: Color(0xFFFBBF24),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'arXiv temporarily limited',
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w700,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  'Showing available source-backed results.',
                  style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: AppColors.textSecondary,
                      ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

class _SummaryChip extends StatelessWidget {
  const _SummaryChip({
    required this.label,
    required this.value,
  });

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.surface.withValues(alpha: 0.92),
        borderRadius: BorderRadius.circular(999),
        border: Border.all(
          color: AppColors.border.withValues(alpha: 0.9),
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(
            value,
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: AppColors.textPrimary,
                  fontWeight: FontWeight.w800,
                ),
          ),
          const SizedBox(width: 8),
          Text(
            label,
            style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: AppColors.textSecondary,
                  fontWeight: FontWeight.w600,
                ),
          ),
        ],
      ),
    );
  }
}
