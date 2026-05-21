import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_config.dart';
import '../data/local_user_store.dart';
import '../models/app_user.dart';
import '../models/generated_project.dart';
import '../services/api_service.dart';
import '../widgets/app_button.dart';
import '../widgets/app_text_field.dart';
import '../widgets/empty_state.dart';
import '../widgets/glass_card.dart';
import '../widgets/loading_view.dart';
import '../widgets/project_card.dart';
import 'blueprint_screen.dart';
import 'project_chat_screen.dart';
import 'project_details_screen.dart';

class SavedProjectsScreen extends StatefulWidget {
  const SavedProjectsScreen({super.key});

  @override
  State<SavedProjectsScreen> createState() => _SavedProjectsScreenState();
}

class _SavedProjectsScreenState extends State<SavedProjectsScreen> {
  final _apiService = const ApiService();
  final _userStore = const LocalUserStore();
  final _searchController = TextEditingController();

  List<GeneratedProject> _projects = <GeneratedProject>[];
  final Map<String, Object> _favoriteIdsByProjectId = <String, Object>{};
  AppUser? _currentUser;
  _ProjectFilter _filter = _ProjectFilter.all;
  bool _isLoading = true;
  bool _isSearching = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  List<GeneratedProject> get _filteredProjects {
    switch (_filter) {
      case _ProjectFilter.all:
        return _projects;
      case _ProjectFilter.verified:
        return _projects
            .where((project) => project.sourceStatus == 'real_sources')
            .toList();
      case _ProjectFilter.paperOnly:
        return _projects
            .where((project) => project.sourceStatus == 'paper_only')
            .toList();
      case _ProjectFilter.repoOnly:
        return _projects
            .where((project) => project.sourceStatus == 'repo_only')
            .toList();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Saved Projects'),
        backgroundColor: Colors.transparent,
      ),
      body: Container(
        decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
        child: SafeArea(top: false, child: _buildBody()),
      ),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Padding(
        padding: EdgeInsets.all(24),
        child: LoadingView(
          title: 'Loading Saved Projects',
          lines: ['Fetching your project library...'],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadProjects,
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: AppConfig.contentMaxWidth),
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              _SearchAndFilters(
                controller: _searchController,
                filter: _filter,
                isSearching: _isSearching,
                onSearch: _handleSearch,
                onFilterChanged: (filter) {
                  setState(() {
                    _filter = filter;
                  });
                },
              ),
              if (_errorMessage != null) ...[
                const SizedBox(height: 14),
                _ErrorBanner(message: _errorMessage!),
              ],
              const SizedBox(height: 16),
              if (_filteredProjects.isEmpty)
                const EmptyState(
                  title: 'No saved projects yet.',
                  message: 'Save generated ideas to build your project library.',
                  icon: Icons.bookmark_outline_rounded,
                )
              else
                ..._filteredProjects.map(
                  (project) => Padding(
                    padding: const EdgeInsets.only(bottom: 16),
                    child: ProjectCard(
                      project: project,
                      isFavorite:
                          _favoriteIdsByProjectId.containsKey(project.id),
                      onDetails: () => _openDetails(project),
                      onChat: () => _openChat(project),
                      onBlueprint: () => _openBlueprint(project),
                      onEdit: () => _showEditProjectSheet(project),
                      onDelete: () => _confirmDelete(project),
                      onFavorite: () => _toggleFavorite(project),
                    ),
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _loadInitialData() async {
    final user = await _userStore.getCurrentUser();
    if (!mounted) {
      return;
    }
    setState(() {
      _currentUser = user;
    });
    await _loadProjects();
    await _loadFavorites();
  }

  Future<void> _loadProjects() async {
    try {
      final projects = await _apiService.getSavedProjects();
      if (!mounted) {
        return;
      }
      setState(() {
        _projects = projects;
        _errorMessage = null;
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

  Future<void> _loadFavorites() async {
    final userId = _coerceId(_currentUser?.id);
    if (userId == null) {
      return;
    }

    try {
      final favorites = await _apiService.getFavorites(userId);
      if (!mounted) {
        return;
      }
      setState(() {
        _favoriteIdsByProjectId
          ..clear()
          ..addEntries(
            favorites.map((favorite) {
              final projectId =
                  (favorite['project_id'] ?? favorite['projectId']).toString();
              final favoriteId =
                  favorite['favorite_id'] ?? favorite['id'] ?? projectId;
              return MapEntry(projectId, favoriteId as Object);
            }).where((entry) => entry.key.trim().isNotEmpty),
          );
      });
    } catch (_) {
      // Favorites should not block saved projects.
    }
  }

  Future<void> _handleSearch() async {
    final query = _searchController.text.trim();
    setState(() {
      _isSearching = true;
      _errorMessage = null;
    });

    try {
      final projects = query.isEmpty
          ? await _apiService.getSavedProjects()
          : await _apiService.searchProjects(query);
      if (!mounted) {
        return;
      }
      setState(() {
        _projects = projects;
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
          _isSearching = false;
        });
      }
    }
  }

  Future<void> _toggleFavorite(GeneratedProject project) async {
    final userId = _coerceId(_currentUser?.id);
    if (userId == null) {
      _showSnack('Please login first.');
      return;
    }

    try {
      final existingFavoriteId = _favoriteIdsByProjectId[project.id];
      if (existingFavoriteId != null) {
        await _apiService.deleteFavorite(existingFavoriteId);
        if (!mounted) {
          return;
        }
        setState(() {
          _favoriteIdsByProjectId.remove(project.id);
        });
        _showSnack('Removed from favorites.');
        return;
      }

      final response = await _apiService.addFavorite(userId, project.id);
      final favorite = response['favorite'] is Map
          ? Map<String, dynamic>.from(response['favorite'] as Map)
          : response;
      final favoriteId = favorite['favorite_id'] ?? favorite['id'] ?? project.id;
      if (!mounted) {
        return;
      }
      setState(() {
        _favoriteIdsByProjectId[project.id] = favoriteId as Object;
      });
      _showSnack('Added to favorites.');
    } on ApiException catch (error) {
      _showSnack(error.message);
    }
  }

  Future<void> _confirmDelete(GeneratedProject project) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete project?'),
        content: Text('Remove "${project.title}" from saved projects.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            onPressed: () => Navigator.of(context).pop(true),
            child: const Text('Delete'),
          ),
        ],
      ),
    );

    if (confirmed != true) {
      return;
    }

    try {
      await _apiService.deleteProject(project.id);
      if (!mounted) {
        return;
      }
      setState(() {
        _projects.removeWhere((item) => item.id == project.id);
      });
      _showSnack('Project deleted.');
    } on ApiException catch (error) {
      _showSnack(error.message);
    }
  }

  Future<void> _showEditProjectSheet(GeneratedProject project) async {
    final titleController = TextEditingController(text: project.title);
    final categoryController = TextEditingController(text: project.category);
    final difficultyController = TextEditingController(text: project.difficulty);
    final descriptionController = TextEditingController(text: project.description);
    final durationController = TextEditingController(
      text: project.durationMonths?.toString() ?? '',
    );

    final updated = await showModalBottomSheet<GeneratedProject>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.background,
      builder: (context) => _EditProjectSheet(
        titleController: titleController,
        categoryController: categoryController,
        difficultyController: difficultyController,
        descriptionController: descriptionController,
        durationController: durationController,
        onSave: () async {
          final title = titleController.text.trim();
          if (title.length < 3) {
            _showSnack('Project title must be at least 3 characters.');
            return null;
          }
          return _apiService.updateProject(project.id, {
            'title': title,
            'category': categoryController.text.trim(),
            'difficulty': difficultyController.text.trim(),
            'description': descriptionController.text.trim(),
            'duration_months': int.tryParse(durationController.text.trim()),
          });
        },
      ),
    );

    titleController.dispose();
    categoryController.dispose();
    difficultyController.dispose();
    descriptionController.dispose();
    durationController.dispose();

    if (updated == null || !mounted) {
      return;
    }

    setState(() {
      final index = _projects.indexWhere((item) => item.id == project.id);
      if (index == -1) {
        _projects.add(updated);
      } else {
        _projects[index] = updated;
      }
    });
    _showSnack('Project updated.');
  }

  void _openDetails(GeneratedProject project) {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => ProjectDetailsScreen(project: project)),
    );
  }

  void _openChat(GeneratedProject project) {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => ProjectChatScreen(project: project)),
    );
  }

  void _openBlueprint(GeneratedProject project) {
    Navigator.of(context).push(
      MaterialPageRoute(builder: (_) => BlueprintScreen(project: project)),
    );
  }

  Object? _coerceId(String? id) {
    if (id == null || id.trim().isEmpty) {
      return null;
    }
    return int.tryParse(id.trim()) ?? id.trim();
  }

  void _showSnack(String message) {
    if (!mounted) {
      return;
    }
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(message)),
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

class _SearchAndFilters extends StatelessWidget {
  const _SearchAndFilters({
    required this.controller,
    required this.filter,
    required this.isSearching,
    required this.onSearch,
    required this.onFilterChanged,
  });

  final TextEditingController controller;
  final _ProjectFilter filter;
  final bool isSearching;
  final VoidCallback onSearch;
  final ValueChanged<_ProjectFilter> onFilterChanged;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(18),
      child: Column(
        children: [
          Row(
            children: [
              Expanded(
                child: TextField(
                  controller: controller,
                  textInputAction: TextInputAction.search,
                  onSubmitted: (_) => onSearch(),
                  decoration: const InputDecoration(
                    hintText: 'Search saved projects...',
                    prefixIcon: Icon(Icons.search_rounded),
                  ),
                ),
              ),
              const SizedBox(width: 10),
              IconButton.filled(
                tooltip: 'Search',
                onPressed: isSearching ? null : onSearch,
                icon: isSearching
                    ? const SizedBox(
                        height: 18,
                        width: 18,
                        child: CircularProgressIndicator(strokeWidth: 2),
                      )
                    : const Icon(Icons.search_rounded),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Align(
            alignment: Alignment.centerLeft,
            child: Wrap(
              spacing: 8,
              runSpacing: 8,
              children: _ProjectFilter.values.map((item) {
                return ChoiceChip(
                  label: Text(item.label),
                  selected: filter == item,
                  onSelected: (_) => onFilterChanged(item),
                );
              }).toList(),
            ),
          ),
        ],
      ),
    );
  }
}

class _EditProjectSheet extends StatefulWidget {
  const _EditProjectSheet({
    required this.titleController,
    required this.categoryController,
    required this.difficultyController,
    required this.descriptionController,
    required this.durationController,
    required this.onSave,
  });

  final TextEditingController titleController;
  final TextEditingController categoryController;
  final TextEditingController difficultyController;
  final TextEditingController descriptionController;
  final TextEditingController durationController;
  final Future<GeneratedProject?> Function() onSave;

  @override
  State<_EditProjectSheet> createState() => _EditProjectSheetState();
}

class _EditProjectSheetState extends State<_EditProjectSheet> {
  bool _isSaving = false;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: SingleChildScrollView(
        padding: EdgeInsets.fromLTRB(
          24,
          24,
          24,
          24 + MediaQuery.of(context).viewInsets.bottom,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            AppTextField(
              label: 'Title',
              hint: 'Project title',
              controller: widget.titleController,
              prefixIcon: Icons.title_rounded,
            ),
            const SizedBox(height: 14),
            AppTextField(
              label: 'Category',
              hint: 'AI, Healthcare...',
              controller: widget.categoryController,
              prefixIcon: Icons.category_outlined,
            ),
            const SizedBox(height: 14),
            AppTextField(
              label: 'Difficulty',
              hint: 'Beginner, Intermediate...',
              controller: widget.difficultyController,
              prefixIcon: Icons.speed_rounded,
            ),
            const SizedBox(height: 14),
            AppTextField(
              label: 'Duration Months',
              hint: '5',
              controller: widget.durationController,
              prefixIcon: Icons.calendar_month_outlined,
              keyboardType: TextInputType.number,
            ),
            const SizedBox(height: 14),
            AppTextField(
              label: 'Description',
              hint: 'Short practical summary',
              controller: widget.descriptionController,
              prefixIcon: Icons.notes_rounded,
              maxLines: 4,
            ),
            const SizedBox(height: 18),
            AppButton(
              label: 'Save Changes',
              icon: Icons.save_outlined,
              isLoading: _isSaving,
              onPressed: _isSaving
                  ? null
                  : () async {
                      setState(() {
                        _isSaving = true;
                      });
                      try {
                        final project = await widget.onSave();
                        if (context.mounted && project != null) {
                          Navigator.of(context).pop(project);
                        }
                      } on ApiException catch (error) {
                        if (context.mounted) {
                          ScaffoldMessenger.of(context).showSnackBar(
                            SnackBar(content: Text(error.message)),
                          );
                        }
                      } finally {
                        if (mounted) {
                          setState(() {
                            _isSaving = false;
                          });
                        }
                      }
                    },
            ),
          ],
        ),
      ),
    );
  }
}

class _ErrorBanner extends StatelessWidget {
  const _ErrorBanner({required this.message});

  final String message;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0x33EF4444),
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: const Color(0x55EF4444)),
      ),
      child: Text(
        message,
        style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: AppColors.textPrimary,
            ),
      ),
    );
  }
}
