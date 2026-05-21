import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../core/app_config.dart';
import '../data/local_user_store.dart';
import '../models/app_user.dart';
import '../models/chat_message.dart';
import '../models/generated_project.dart';
import '../services/api_service.dart';
import '../widgets/chat_bubble.dart';
import '../widgets/glass_card.dart';

class ProjectChatScreen extends StatefulWidget {
  const ProjectChatScreen({
    super.key,
    required this.project,
  });

  final GeneratedProject project;

  @override
  State<ProjectChatScreen> createState() => _ProjectChatScreenState();
}

class _ProjectChatScreenState extends State<ProjectChatScreen> {
  final _apiService = const ApiService();
  final _userStore = const LocalUserStore();
  final _inputController = TextEditingController();
  final _scrollController = ScrollController();

  final List<ChatMessage> _messages = const [
    ChatMessage(
      role: 'assistant',
      content:
          'Ask me anything about this project idea, scope, architecture, timeline, or presentation.',
    ),
  ].toList();

  AppUser? _currentUser;
  Object? _sessionId;
  bool _isSending = false;

  static const _suggestions = [
    'Explain simply',
    'Divide tasks for 3 members',
    'Architecture',
    'Presentation questions',
    'Risks',
    'API endpoints',
  ];

  @override
  void initState() {
    super.initState();
    _loadCurrentUser();
  }

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Chat with Project AI'),
        backgroundColor: Colors.transparent,
      ),
      body: Container(
        decoration: const BoxDecoration(gradient: AppColors.backgroundGradient),
        child: SafeArea(
          top: false,
          child: Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: AppConfig.contentMaxWidth),
              child: Column(
                children: [
                  Padding(
                    padding: const EdgeInsets.fromLTRB(24, 12, 24, 10),
                    child: _ProjectMiniHeader(project: widget.project),
                  ),
                  Expanded(
                    child: ListView.builder(
                      controller: _scrollController,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 8,
                      ),
                      itemCount: _messages.length + (_isSending ? 1 : 0),
                      itemBuilder: (context, index) {
                        if (_isSending && index == _messages.length) {
                          return const ChatBubble(
                            text: '',
                            isUser: false,
                            isLoading: true,
                          );
                        }
                        final message = _messages[index];
                        return ChatBubble(
                          text: message.content,
                          isUser: message.isUser,
                        );
                      },
                    ),
                  ),
                  _SuggestionChips(
                    suggestions: _suggestions,
                    onSelected: _sendText,
                  ),
                  _InputBar(
                    controller: _inputController,
                    isSending: _isSending,
                    onSend: () => _sendText(_inputController.text),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Future<void> _loadCurrentUser() async {
    final user = await _userStore.getCurrentUser();
    if (!mounted) {
      return;
    }
    setState(() {
      _currentUser = user;
    });
  }

  Future<void> _sendText(String rawText) async {
    final text = rawText.trim();
    if (text.isEmpty || _isSending) {
      return;
    }

    _inputController.clear();
    setState(() {
      _messages.add(ChatMessage(role: 'user', content: text));
      _isSending = true;
    });
    _scrollToBottom();

    try {
      final response = await _apiService.chatWithProject(
        widget.project,
        _messages.map((message) => message.toJson()).toList(),
        userId: _coerceId(_currentUser?.id),
        sessionId: _sessionId,
      );

      final reply = _readReply(response);
      final returnedSessionId = response['session_id'] ?? response['sessionId'];
      if (!mounted) {
        return;
      }
      setState(() {
        if (returnedSessionId != null) {
          _sessionId = returnedSessionId;
        }
        _messages.add(
          ChatMessage(
            role: 'assistant',
            content: reply.isEmpty
                ? 'I received the response, but no reply text was returned.'
                : reply,
          ),
        );
      });
    } on ApiException catch (error) {
      if (!mounted) {
        return;
      }
      setState(() {
        _messages.add(
          ChatMessage(
            role: 'assistant',
            content:
                'I cannot reach the project AI right now. ${error.message}',
          ),
        );
      });
    } finally {
      if (mounted) {
        setState(() {
          _isSending = false;
        });
        _scrollToBottom();
      }
    }
  }

  String _readReply(Map<String, dynamic> response) {
    for (final key in const ['reply', 'message', 'answer', 'content']) {
      final value = response[key];
      if (value != null && value.toString().trim().isNotEmpty) {
        return value.toString().trim();
      }
    }
    return '';
  }

  Object? _coerceId(String? id) {
    if (id == null || id.trim().isEmpty) {
      return null;
    }
    return int.tryParse(id.trim()) ?? id.trim();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) {
        return;
      }
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOut,
      );
    });
  }
}

class _ProjectMiniHeader extends StatelessWidget {
  const _ProjectMiniHeader({required this.project});

  final GeneratedProject project;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(16),
      borderRadius: 20,
      child: Row(
        children: [
          Container(
            height: 42,
            width: 42,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(15),
              gradient: AppColors.primaryGradient,
            ),
            child: const Icon(
              Icons.psychology_alt_rounded,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  project.title,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        color: AppColors.textPrimary,
                        fontWeight: FontWeight.w800,
                      ),
                ),
                const SizedBox(height: 4),
                Text(
                  '${project.category} - ${_sourceLabel(project.sourceStatus)}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
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

  String _sourceLabel(String status) {
    switch (status.toLowerCase()) {
      case 'real_sources':
        return 'Verified';
      case 'paper_only':
        return 'Paper Only';
      case 'repo_only':
        return 'Repo Only';
      default:
        return 'Source Review';
    }
  }
}

class _SuggestionChips extends StatelessWidget {
  const _SuggestionChips({
    required this.suggestions,
    required this.onSelected,
  });

  final List<String> suggestions;
  final void Function(String text) onSelected;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 48,
      child: ListView.separated(
        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 4),
        scrollDirection: Axis.horizontal,
        itemBuilder: (context, index) {
          final suggestion = suggestions[index];
          return ActionChip(
            label: Text(suggestion),
            onPressed: () => onSelected(suggestion),
          );
        },
        separatorBuilder: (_, _) => const SizedBox(width: 8),
        itemCount: suggestions.length,
      ),
    );
  }
}

class _InputBar extends StatelessWidget {
  const _InputBar({
    required this.controller,
    required this.isSending,
    required this.onSend,
  });

  final TextEditingController controller;
  final bool isSending;
  final VoidCallback onSend;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(
        24,
        8,
        24,
        12 + MediaQuery.of(context).viewInsets.bottom,
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: controller,
              minLines: 1,
              maxLines: 4,
              textInputAction: TextInputAction.newline,
              decoration: InputDecoration(
                hintText: 'Ask about scope, tasks, APIs...',
                filled: true,
                fillColor: AppColors.surface.withValues(alpha: 0.88),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(18),
                  borderSide: const BorderSide(color: AppColors.border),
                ),
                enabledBorder: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(18),
                  borderSide: const BorderSide(color: AppColors.border),
                ),
              ),
            ),
          ),
          const SizedBox(width: 10),
          IconButton.filled(
            tooltip: 'Send',
            onPressed: isSending ? null : onSend,
            icon: isSending
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.send_rounded),
          ),
        ],
      ),
    );
  }
}
