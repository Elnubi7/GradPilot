import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_config.dart';
import '../models/generated_project.dart';
import '../services/api_service.dart';
import '../widgets/app_button.dart';
import '../widgets/app_text_field.dart';
import '../widgets/empty_state.dart';
import '../widgets/loading_view.dart';
import '../widgets/project_card.dart';
import 'project_chat_screen.dart';
import 'project_details_screen.dart';

class SearchScreen extends StatefulWidget {
  const SearchScreen({super.key});

  @override
  State<SearchScreen> createState() => _SearchScreenState();
}

class _SearchScreenState extends State<SearchScreen> {
  final _apiService = const ApiService();
  final _searchController = TextEditingController();

  List<GeneratedProject> _results = <GeneratedProject>[];
  bool _isLoading = false;
  bool _hasSearched = false;
  String? _errorMessage;

  static const _suggestions = [
    'AI',
    'Healthcare',
    'Agriculture',
    'Education',
    'Cybersecurity',
    'Flutter',
  ];

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Search Projects'),
        backgroundColor: Colors.transparent,
      ),
      body: Container(
        decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
        child: SafeArea(
          top: false,
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: AppConfig.contentMaxWidth),
              child: ListView(
                padding: const EdgeInsets.all(24),
                children: [
                  AppTextField(
                    label: 'Search',
                    hint: 'Search saved projects by topic or stack...',
                    controller: _searchController,
                    prefixIcon: Icons.search_rounded,
                    textInputAction: TextInputAction.search,
                  ),
                  const SizedBox(height: 14),
                  AppButton(
                    label: 'Search',
                    icon: Icons.travel_explore_rounded,
                    isLoading: _isLoading,
                    onPressed: _isLoading ? null : _search,
                  ),
                  const SizedBox(height: 14),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: _suggestions.map((suggestion) {
                      return ActionChip(
                        label: Text(suggestion),
                        onPressed: () {
                          _searchController.text = suggestion;
                          _search();
                        },
                      );
                    }).toList(),
                  ),
                  if (_errorMessage != null) ...[
                    const SizedBox(height: 16),
                    Text(
                      _errorMessage!,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                            color: const Color(0xFFFCA5A5),
                          ),
                    ),
                  ],
                  const SizedBox(height: 20),
                  if (_isLoading)
                    const LoadingView(
                      title: 'Searching Projects',
                      lines: ['Checking saved projects...'],
                    )
                  else if (_results.isEmpty)
                    EmptyState(
                      title: _hasSearched ? 'No matching projects.' : 'Search saved projects.',
                      message: _hasSearched
                          ? 'Try a broader topic or a different stack keyword.'
                          : 'Use topic, department, or technology keywords.',
                      icon: _hasSearched
                          ? Icons.search_off_rounded
                          : Icons.search_rounded,
                    )
                  else
                    ..._results.map(
                      (project) => Padding(
                        padding: const EdgeInsets.only(bottom: 16),
                        child: ProjectCard(
                          project: project,
                          onDetails: () => Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) =>
                                  ProjectDetailsScreen(project: project),
                            ),
                          ),
                          onChat: () => Navigator.of(context).push(
                            MaterialPageRoute(
                              builder: (_) => ProjectChatScreen(project: project),
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
    );
  }

  Future<void> _search() async {
    final query = _searchController.text.trim();
    if (query.isEmpty) {
      return;
    }

    setState(() {
      _isLoading = true;
      _hasSearched = true;
      _errorMessage = null;
    });

    try {
      final results = await _apiService.searchProjects(query);
      if (!mounted) {
        return;
      }
      setState(() {
        _results = results;
      });
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _errorMessage = error.message;
        _results = <GeneratedProject>[];
      });
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }
}
