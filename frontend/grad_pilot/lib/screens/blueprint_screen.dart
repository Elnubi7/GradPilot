import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_config.dart';
import '../models/generated_project.dart';
import '../services/api_service.dart';
import '../widgets/app_button.dart';
import '../widgets/glass_card.dart';
import '../widgets/loading_view.dart';
import '../widgets/section_card.dart';
import 'markdown_preview_screen.dart';

class BlueprintScreen extends StatefulWidget {
  const BlueprintScreen({
    super.key,
    required this.project,
  });

  final GeneratedProject project;

  @override
  State<BlueprintScreen> createState() => _BlueprintScreenState();
}

class _BlueprintScreenState extends State<BlueprintScreen> {
  final _apiService = const ApiService();

  bool _isLoading = true;
  bool _isExporting = false;
  String? _errorMessage;
  Map<String, dynamic> _blueprint = <String, dynamic>{};

  static const _preferredOrder = [
    'refined_problem_statement',
    'objectives',
    'target_users',
    'core_features',
    'optional_features',
    'system_architecture',
    'backend_modules',
    'flutter_screens',
    'database_or_storage_plan',
    'api_endpoints',
    'ai_pipeline',
    'weekly_milestones',
    'evaluation_metrics',
    'risks',
    'presentation_outline',
    'source_links',
  ];

  @override
  void initState() {
    super.initState();
    _loadBlueprint();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Project Blueprint'),
        backgroundColor: Colors.transparent,
        actions: [
          if (_blueprint.isNotEmpty)
            Padding(
              padding: const EdgeInsetsDirectional.only(end: 12),
              child: TextButton.icon(
                onPressed: _isExporting ? null : _handleExport,
                icon: _isExporting
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.article_outlined),
                label: const Text('Export'),
              ),
            ),
        ],
      ),
      body: Container(
        decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
        child: SafeArea(
          top: false,
          child: AnimatedSwitcher(
            duration: const Duration(milliseconds: 220),
            child: _buildBody(context),
          ),
        ),
      ),
    );
  }

  Widget _buildBody(BuildContext context) {
    if (_isLoading) {
      return const Padding(
        key: ValueKey('loading'),
        padding: EdgeInsets.all(24),
        child: LoadingView(
          title: 'Building Blueprint',
          lines: [
            'Structuring features, architecture, and timeline...',
            'Preparing advisor-ready project sections...',
          ],
        ),
      );
    }

    if (_errorMessage != null) {
      return Center(
        key: const ValueKey('error'),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: AppConfig.contentMaxWidth),
            child: GlassCard(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Icon(
                    Icons.error_outline_rounded,
                    color: Color(0xFFF87171),
                    size: 42,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    _errorMessage!,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyLarge,
                  ),
                  const SizedBox(height: 18),
                  AppButton(
                    label: 'Retry',
                    icon: Icons.refresh_rounded,
                    onPressed: _loadBlueprint,
                  ),
                ],
              ),
            ),
          ),
        ),
      );
    }

    final entries = _orderedEntries();
    return Center(
      key: const ValueKey('content'),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: AppConfig.contentMaxWidth),
        child: ListView.separated(
          padding: const EdgeInsets.all(24),
          itemCount: entries.length + 1,
          separatorBuilder: (_, _) => const SizedBox(height: 14),
          itemBuilder: (context, index) {
            if (index == 0) {
              return _BlueprintHeader(project: widget.project);
            }
            final entry = entries[index - 1];
            return SectionCard(
              title: _humanize(entry.key),
              child: _DynamicValueView(value: entry.value),
            );
          },
        ),
      ),
    );
  }

  Future<void> _loadBlueprint() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final blueprint = await _apiService.generateBlueprint(widget.project);
      if (!mounted) {
        return;
      }
      setState(() {
        _blueprint = blueprint;
      });
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _errorMessage = error.message;
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  Future<void> _handleExport() async {
    setState(() {
      _isExporting = true;
    });

    try {
      final markdown = await _apiService.exportMarkdown(widget.project);
      if (!mounted) {
        return;
      }
      Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => MarkdownPreviewScreen(markdown: markdown),
        ),
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
          _isExporting = false;
        });
      }
    }
  }

  List<MapEntry<String, dynamic>> _orderedEntries() {
    final entries = <MapEntry<String, dynamic>>[];
    for (final key in _preferredOrder) {
      if (_blueprint.containsKey(key)) {
        entries.add(MapEntry(key, _blueprint[key]));
      }
    }
    for (final entry in _blueprint.entries) {
      if (!_preferredOrder.contains(entry.key)) {
        entries.add(entry);
      }
    }
    return entries.where((entry) => !_isEmptyValue(entry.value)).toList();
  }

  bool _isEmptyValue(dynamic value) {
    if (value == null) {
      return true;
    }
    if (value is String) {
      return value.trim().isEmpty;
    }
    if (value is Iterable) {
      return value.isEmpty;
    }
    if (value is Map) {
      return value.isEmpty;
    }
    return false;
  }
}

class _BlueprintHeader extends StatelessWidget {
  const _BlueprintHeader({required this.project});

  final GeneratedProject project;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            project.title,
            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                  fontWeight: FontWeight.w800,
                  fontSize: 28,
                ),
          ),
          const SizedBox(height: 10),
          Text(
            project.description,
            style: Theme.of(context).textTheme.bodyLarge,
          ),
        ],
      ),
    );
  }
}

class _DynamicValueView extends StatelessWidget {
  const _DynamicValueView({required this.value});

  final dynamic value;

  @override
  Widget build(BuildContext context) {
    if (value is List) {
      return BulletList(items: value.map((item) => item.toString()).toList());
    }
    if (value is Map) {
      final entries = Map<String, dynamic>.from(value as Map).entries.toList();
      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: entries.map((entry) {
          return Container(
            width: double.infinity,
            margin: const EdgeInsets.only(bottom: 10),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: AppColors.surface.withValues(alpha: 0.72),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.border.withValues(alpha: 0.8)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  _humanize(entry.key),
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 8),
                _DynamicValueView(value: entry.value),
              ],
            ),
          );
        }).toList(),
      );
    }

    return Text(
      value?.toString().trim().isNotEmpty ?? false
          ? value.toString().trim()
          : 'Not provided yet.',
      style: Theme.of(context).textTheme.bodyMedium,
    );
  }
}

String _humanize(String key) {
  return key
      .replaceAll('_', ' ')
      .split(' ')
      .where((word) => word.isNotEmpty)
      .map((word) => '${word[0].toUpperCase()}${word.substring(1)}')
      .join(' ');
}
