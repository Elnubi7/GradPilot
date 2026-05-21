import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_config.dart';
import '../core/app_routes.dart';
import '../data/local_user_store.dart';
import '../models/app_user.dart';
import '../services/api_service.dart';
import '../widgets/empty_state.dart';
import '../widgets/glass_card.dart';
import '../widgets/stat_card.dart';
import 'saved_projects_screen.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});

  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  final _userStore = const LocalUserStore();
  final _apiService = const ApiService();

  AppUser? _currentUser;
  int _savedCount = 0;
  int _favoritesCount = 0;
  int _chatSessionsCount = 0;
  List<Map<String, dynamic>> _chatSessions = <Map<String, dynamic>>[];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadProfile();
  }

  @override
  Widget build(BuildContext context) {
    final user = _currentUser;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Profile'),
        backgroundColor: Colors.transparent,
      ),
      body: Container(
        decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
        child: SafeArea(
          top: false,
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: AppConfig.contentMaxWidth),
              child: RefreshIndicator(
                onRefresh: _loadProfile,
                child: ListView(
                  padding: const EdgeInsets.all(24),
                  children: [
                    GlassCard(
                      child: Column(
                        children: [
                          CircleAvatar(
                            radius: 38,
                            backgroundColor: AppColors.primary,
                            child: Text(
                              _initials(user?.fullName),
                              style: Theme.of(context)
                                  .textTheme
                                  .headlineMedium
                                  ?.copyWith(fontWeight: FontWeight.w800),
                            ),
                          ),
                          const SizedBox(height: 16),
                          Text(
                            user?.fullName ?? 'Guest User',
                            textAlign: TextAlign.center,
                            style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                                  fontWeight: FontWeight.w800,
                                  fontSize: 28,
                                ),
                          ),
                          const SizedBox(height: 6),
                          Text(user?.email ?? 'No active session'),
                          const SizedBox(height: 10),
                          Chip(
                            label: Text(user?.department ?? 'Department unavailable'),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                    if (_isLoading)
                      const LinearProgressIndicator(minHeight: 3)
                    else
                      Row(
                        children: [
                          Expanded(
                            child: StatCard(
                              label: 'Saved',
                              value: _savedCount.toString(),
                              icon: Icons.bookmark_outline_rounded,
                              compact: true,
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: StatCard(
                              label: 'Favorites',
                              value: _favoritesCount.toString(),
                              icon: Icons.favorite_border_rounded,
                              compact: true,
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            child: StatCard(
                              label: 'Chats',
                              value: _chatSessionsCount.toString(),
                              icon: Icons.chat_bubble_outline_rounded,
                              compact: true,
                            ),
                          ),
                        ],
                      ),
                    const SizedBox(height: 16),
                    _MenuTile(
                      icon: Icons.bookmark_outline_rounded,
                      title: 'Saved Projects',
                      onTap: () => Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => const SavedProjectsScreen(),
                        ),
                      ),
                    ),
                    _MenuTile(
                      icon: Icons.favorite_border_rounded,
                      title: 'Favorites',
                      onTap: _showFavoritesInfo,
                    ),
                    _MenuTile(
                      icon: Icons.history_rounded,
                      title: 'Chat History',
                      onTap: _showChatHistory,
                    ),
                    _MenuTile(
                      icon: Icons.help_outline_rounded,
                      title: 'Help & Support',
                      onTap: () => _showSnack('Contact your department advisor for support.'),
                    ),
                    _MenuTile(
                      icon: Icons.logout_rounded,
                      title: 'Logout',
                      danger: true,
                      onTap: _logout,
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

  Future<void> _loadProfile() async {
    final user = await _userStore.getCurrentUser();
    if (!mounted) {
      return;
    }
    setState(() {
      _currentUser = user;
      _isLoading = true;
    });

    try {
      final projectsFuture = _apiService.getSavedProjects();
      final userId = _coerceId(user?.id);
      final favoritesFuture = userId == null
          ? Future.value(<Map<String, dynamic>>[])
          : _apiService.getFavorites(userId);
      final sessionsFuture = userId == null
          ? Future.value(<Map<String, dynamic>>[])
          : _apiService.getChatSessions(userId);

      final projects = await projectsFuture;
      final favorites = await favoritesFuture;
      final sessions = await sessionsFuture;

      if (!mounted) {
        return;
      }
      setState(() {
        _savedCount = projects.length;
        _favoritesCount = favorites.length;
        _chatSessions = sessions;
        _chatSessionsCount = sessions.length;
      });
    } catch (_) {
      // Profile should still render even when summary endpoints are offline.
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  void _showChatHistory() {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: AppColors.background,
      builder: (context) {
        if (_chatSessions.isEmpty) {
          return const SafeArea(
            child: Padding(
              padding: EdgeInsets.all(24),
              child: EmptyState(
                title: 'No chat history yet.',
                message: 'Project chats will appear here after the backend saves sessions.',
                icon: Icons.history_rounded,
              ),
            ),
          );
        }

        return SafeArea(
          child: ListView.separated(
            padding: const EdgeInsets.all(24),
            itemBuilder: (context, index) {
              final session = _chatSessions[index];
              final title = (session['title'] ??
                      session['project_title'] ??
                      session['project_id'] ??
                      'Chat Session')
                  .toString();
              final sessionId = session['session_id'] ?? session['id'];
              return ListTile(
                title: Text(title),
                subtitle: Text(sessionId == null ? 'Session' : 'ID: $sessionId'),
                trailing: IconButton(
                  tooltip: 'Delete session',
                  icon: const Icon(Icons.delete_outline_rounded),
                  onPressed: sessionId == null
                      ? null
                      : () async {
                          await _apiService.deleteChatSession(sessionId);
                          if (mounted) {
                            Navigator.of(context).pop();
                            await _loadProfile();
                          }
                        },
                ),
              );
            },
            separatorBuilder: (_, _) => const Divider(),
            itemCount: _chatSessions.length,
          ),
        );
      },
    );
  }

  void _showFavoritesInfo() {
    _showSnack(
      _favoritesCount == 0
          ? 'No favorites yet.'
          : 'Favorites are marked in Saved Projects.',
    );
  }

  Future<void> _logout() async {
    await _userStore.logout();
    if (!mounted) {
      return;
    }
    Navigator.of(context).pushNamedAndRemoveUntil(
      AppRoutes.login,
      (route) => false,
    );
  }

  String _initials(String? fullName) {
    final parts = (fullName ?? 'GP')
        .trim()
        .split(RegExp(r'\s+'))
        .where((part) => part.isNotEmpty)
        .toList();
    if (parts.isEmpty) {
      return 'GP';
    }
    return parts.take(2).map((part) => part[0].toUpperCase()).join();
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

class _MenuTile extends StatelessWidget {
  const _MenuTile({
    required this.icon,
    required this.title,
    required this.onTap,
    this.danger = false,
  });

  final IconData icon;
  final String title;
  final VoidCallback onTap;
  final bool danger;

  @override
  Widget build(BuildContext context) {
    final color = danger ? const Color(0xFFF87171) : AppColors.textPrimary;

    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: GlassCard(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        borderRadius: 18,
        child: ListTile(
          contentPadding: EdgeInsets.zero,
          leading: Icon(icon, color: color),
          title: Text(
            title,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  color: color,
                  fontWeight: FontWeight.w700,
                ),
          ),
          trailing: const Icon(Icons.chevron_right_rounded),
          onTap: onTap,
        ),
      ),
    );
  }
}
