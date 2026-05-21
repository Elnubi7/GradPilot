import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import '../core/app_config.dart';
import '../models/app_user.dart';
import '../models/auth_response.dart';
import '../models/generated_project.dart';
import '../models/generated_projects_response.dart';

class ApiService {
  const ApiService();

  Future<AppUser> register({
    required String fullName,
    required String email,
    required String phone,
    required String department,
    required String password,
    String avatarStyle = 'blue',
  }) async {
    final response = await _postMap(
      '/users/register',
      timeout: const Duration(seconds: 20),
      body: {
        'full_name': fullName.trim(),
        'email': email.trim().toLowerCase(),
        'phone': phone.trim(),
        'department': department.trim(),
        'password': password,
        'avatar_style': avatarStyle,
      },
      defaultErrorMessage: 'Unable to create your account right now.',
    );

    return AppUser.fromJson(response);
  }

  Future<AuthResponse> login({
    required String email,
    required String password,
  }) async {
    final response = await _postMap(
      '/users/login',
      timeout: const Duration(seconds: 20),
      body: {
        'email': email.trim().toLowerCase(),
        'password': password,
      },
      defaultErrorMessage: 'Invalid email or password.',
    );

    return AuthResponse.fromJson(response);
  }

  Future<GeneratedProjectsResponse> generateProjects({
    required String promptText,
    int maxResults = 5,
  }) async {
    final response = await _postMap(
      '/advisor/generate-projects',
      timeout: const Duration(seconds: 60),
      body: {
        'interests': <String>[],
        'level': '',
        'duration_months': null,
        'preferred_stack': <String>[],
        'prompt_text': promptText.trim(),
        'project_type': '',
        'max_results': maxResults,
      },
      defaultErrorMessage: 'Unable to generate project ideas right now.',
    );

    return GeneratedProjectsResponse.fromJson(response);
  }

  Future<String> saveGeneratedProject(GeneratedProject project) async {
    final response = await _postMap(
      '/projects/save-generated',
      timeout: const Duration(seconds: 20),
      body: project.toJson(),
      defaultErrorMessage: 'Unable to save this project right now.',
    );

    final message = _readMessageFromDecoded(response);
    if (message != null && message.isNotEmpty) {
      return message;
    }
    return 'Project saved successfully';
  }

  Future<List<AppUser>> getUsers() async {
    final decoded = await _getJson(
      '/users',
      timeout: const Duration(seconds: 20),
      defaultErrorMessage: 'Unable to load users right now.',
    );

    return _readList(decoded, const ['users'])
        .whereType<Map>()
        .map((item) => AppUser.fromJson(Map<String, dynamic>.from(item)))
        .toList();
  }

  Future<AppUser> updateUser(String id, Map<String, dynamic> body) async {
    final decoded = await _putMap(
      '/users/$id',
      timeout: const Duration(seconds: 20),
      body: body,
      defaultErrorMessage: 'Unable to update this user right now.',
    );
    final rawUser = decoded['user'];
    if (rawUser is Map) {
      return AppUser.fromJson(Map<String, dynamic>.from(rawUser));
    }
    return AppUser.fromJson(decoded);
  }

  Future<String> deleteUser(String id) async {
    final decoded = await _deleteJson(
      '/users/$id',
      timeout: const Duration(seconds: 20),
      defaultErrorMessage: 'Unable to delete this user right now.',
    );
    if (decoded is Map<String, dynamic>) {
      return _readMessageFromDecoded(decoded) ?? 'User deleted successfully';
    }
    return 'User deleted successfully';
  }

  Future<List<GeneratedProject>> getSavedProjects() async {
    final decoded = await _getJson(
      '/projects',
      timeout: const Duration(seconds: 20),
      defaultErrorMessage: 'Unable to load saved projects right now.',
    );
    return _readProjects(decoded);
  }

  Future<List<GeneratedProject>> searchProjects(String query) async {
    final uriQuery = Uri.encodeQueryComponent(query.trim());
    final decoded = await _getJson(
      '/projects/search?q=$uriQuery',
      timeout: const Duration(seconds: 20),
      defaultErrorMessage: 'Unable to search projects right now.',
    );
    return _readProjects(decoded);
  }

  Future<GeneratedProject> getProjectById(String id) async {
    final decoded = await _getJson(
      '/projects/$id',
      timeout: const Duration(seconds: 20),
      defaultErrorMessage: 'Unable to load this project right now.',
    );
    if (decoded is Map) {
      final project = decoded['project'];
      if (project is Map) {
        return GeneratedProject.fromJson(Map<String, dynamic>.from(project));
      }
      return GeneratedProject.fromJson(Map<String, dynamic>.from(decoded));
    }
    throw const ApiException('Received an unexpected project response.');
  }

  Future<GeneratedProject> updateProject(
    String id,
    Map<String, dynamic> body,
  ) async {
    final decoded = await _putMap(
      '/projects/$id',
      timeout: const Duration(seconds: 20),
      body: body,
      defaultErrorMessage: 'Unable to update this project right now.',
    );
    final rawProject = decoded['project'];
    if (rawProject is Map) {
      return GeneratedProject.fromJson(Map<String, dynamic>.from(rawProject));
    }
    return GeneratedProject.fromJson(decoded);
  }

  Future<String> deleteProject(String id) async {
    final decoded = await _deleteJson(
      '/projects/$id',
      timeout: const Duration(seconds: 20),
      defaultErrorMessage: 'Unable to delete this project right now.',
    );
    if (decoded is Map<String, dynamic>) {
      return _readMessageFromDecoded(decoded) ?? 'Project deleted successfully';
    }
    return 'Project deleted successfully';
  }

  Future<Map<String, dynamic>> generateBlueprint(
    GeneratedProject project,
  ) async {
    final decoded = await _postMap(
      '/advisor/blueprint',
      timeout: const Duration(seconds: 60),
      body: project.toJson(),
      defaultErrorMessage: 'Unable to generate the blueprint right now.',
    );
    final rawBlueprint = decoded['blueprint'];
    if (rawBlueprint is Map) {
      return Map<String, dynamic>.from(rawBlueprint);
    }
    return decoded;
  }

  Future<String> exportMarkdown(GeneratedProject project) async {
    final decoded = await _requestJson(
      'POST',
      '/advisor/export-markdown',
      timeout: const Duration(seconds: 60),
      body: project.toJson(),
      defaultErrorMessage: 'Unable to export markdown right now.',
    );

    if (decoded is String && decoded.trim().isNotEmpty) {
      return decoded.trim();
    }
    if (decoded is Map<String, dynamic>) {
      for (final key in const ['markdown', 'content', 'text', 'data']) {
        final value = decoded[key];
        if (value != null && value.toString().trim().isNotEmpty) {
          return value.toString().trim();
        }
      }
      return jsonEncode(decoded);
    }
    return decoded.toString();
  }

  Future<Map<String, dynamic>> chatWithProject(
    GeneratedProject project,
    List<Map<String, dynamic>> messages, {
    Object? userId,
    Object? sessionId,
  }) async {
    return _postMap(
      '/advisor/chat',
      timeout: const Duration(seconds: 60),
      body: {
        'project': project.toJson(),
        'messages': messages,
        if (userId != null) 'user_id': userId,
        if (sessionId != null) 'session_id': sessionId,
      },
      defaultErrorMessage: 'Unable to chat with the project AI right now.',
    );
  }

  Future<Map<String, dynamic>> addFavorite(
    Object userId,
    Object projectId,
  ) async {
    return _postMap(
      '/favorites',
      timeout: const Duration(seconds: 20),
      body: {
        'user_id': userId,
        'project_id': projectId,
      },
      defaultErrorMessage: 'Unable to favorite this project right now.',
    );
  }

  Future<List<Map<String, dynamic>>> getFavorites(Object userId) async {
    final decoded = await _getJson(
      '/favorites?user_id=${Uri.encodeQueryComponent(userId.toString())}',
      timeout: const Duration(seconds: 20),
      defaultErrorMessage: 'Unable to load favorites right now.',
    );
    return _readList(decoded, const ['favorites'])
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
  }

  Future<String> deleteFavorite(Object favoriteId) async {
    final decoded = await _deleteJson(
      '/favorites/$favoriteId',
      timeout: const Duration(seconds: 20),
      defaultErrorMessage: 'Unable to remove this favorite right now.',
    );
    if (decoded is Map<String, dynamic>) {
      return _readMessageFromDecoded(decoded) ?? 'Favorite removed';
    }
    return 'Favorite removed';
  }

  Future<List<Map<String, dynamic>>> getChatSessions(Object userId) async {
    final decoded = await _getJson(
      '/chat/sessions?user_id=${Uri.encodeQueryComponent(userId.toString())}',
      timeout: const Duration(seconds: 20),
      defaultErrorMessage: 'Unable to load chat history right now.',
    );
    return _readList(decoded, const ['sessions', 'chat_sessions'])
        .whereType<Map>()
        .map((item) => Map<String, dynamic>.from(item))
        .toList();
  }

  Future<Map<String, dynamic>> getChatSession(Object sessionId) async {
    final decoded = await _getJson(
      '/chat/sessions/$sessionId',
      timeout: const Duration(seconds: 20),
      defaultErrorMessage: 'Unable to load this chat session right now.',
    );
    if (decoded is Map<String, dynamic>) {
      return decoded;
    }
    if (decoded is Map) {
      return Map<String, dynamic>.from(decoded);
    }
    throw const ApiException('Received an unexpected chat session response.');
  }

  Future<String> deleteChatSession(Object sessionId) async {
    final decoded = await _deleteJson(
      '/chat/sessions/$sessionId',
      timeout: const Duration(seconds: 20),
      defaultErrorMessage: 'Unable to delete this chat session right now.',
    );
    if (decoded is Map<String, dynamic>) {
      return _readMessageFromDecoded(decoded) ?? 'Chat session deleted';
    }
    return 'Chat session deleted';
  }

  Future<Map<String, dynamic>> _postMap(
    String path, {
    required Map<String, dynamic> body,
    required Duration timeout,
    required String defaultErrorMessage,
  }) async {
    final decoded = await _requestJson(
      'POST',
      path,
      timeout: timeout,
      body: body,
      defaultErrorMessage: defaultErrorMessage,
    );

    if (decoded is Map<String, dynamic>) {
      return decoded;
    }
    if (decoded is Map) {
      return Map<String, dynamic>.from(decoded);
    }

    throw const ApiException('Received an unexpected response format.');
  }

  Future<Map<String, dynamic>> _putMap(
    String path, {
    required Map<String, dynamic> body,
    required Duration timeout,
    required String defaultErrorMessage,
  }) async {
    final decoded = await _requestJson(
      'PUT',
      path,
      timeout: timeout,
      body: body,
      defaultErrorMessage: defaultErrorMessage,
    );

    if (decoded is Map<String, dynamic>) {
      return decoded;
    }
    if (decoded is Map) {
      return Map<String, dynamic>.from(decoded);
    }

    throw const ApiException('Received an unexpected response format.');
  }

  Future<dynamic> _getJson(
    String path, {
    required Duration timeout,
    required String defaultErrorMessage,
  }) {
    return _requestJson(
      'GET',
      path,
      timeout: timeout,
      defaultErrorMessage: defaultErrorMessage,
    );
  }

  Future<dynamic> _deleteJson(
    String path, {
    required Duration timeout,
    required String defaultErrorMessage,
  }) {
    return _requestJson(
      'DELETE',
      path,
      timeout: timeout,
      defaultErrorMessage: defaultErrorMessage,
    );
  }

  Future<dynamic> _requestJson(
    String method,
    String path, {
    required Duration timeout,
    required String defaultErrorMessage,
    Map<String, dynamic>? body,
  }) async {
    final uri = Uri.parse('${AppConfig.apiBaseUrl}$path');

    try {
      final request = http.Request(method, uri)
        ..headers.addAll(const {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        });
      if (body != null) {
        request.body = jsonEncode(body);
      }

      final streamedResponse = await request.send().timeout(timeout);
      final response = await http.Response.fromStream(streamedResponse);
      final decoded = _decodeResponseBody(response.body);

      if (response.statusCode < 200 || response.statusCode >= 300) {
        throw ApiException(
          _extractErrorMessage(decoded) ?? defaultErrorMessage,
        );
      }

      return decoded;
    } on ApiException {
      rethrow;
    } on TimeoutException {
      throw const ApiException(
        'The request took too long. Please try again in a moment.',
      );
    } on http.ClientException {
      throw const ApiException(
        'Backend is not running. Please start FastAPI server.',
      );
    } on FormatException {
      throw const ApiException(
        'The backend returned invalid data. Please check the API response.',
      );
    } catch (error) {
      final message = error.toString().toLowerCase();
      if (_isOfflineMessage(message)) {
        throw const ApiException(
          'Backend is not running. Please start FastAPI server.',
        );
      }
      throw ApiException(
        message.isNotEmpty ? defaultErrorMessage : 'Something went wrong.',
      );
    }
  }

  dynamic _decodeResponseBody(String body) {
    if (body.trim().isEmpty) {
      return <String, dynamic>{};
    }
    return jsonDecode(body);
  }

  List<dynamic> _readList(dynamic decoded, List<String> wrapperKeys) {
    if (decoded is List) {
      return decoded;
    }
    if (decoded is Map) {
      for (final key in wrapperKeys) {
        final value = decoded[key];
        if (value is List) {
          return value;
        }
      }
      for (final value in decoded.values) {
        if (value is List) {
          return value;
        }
      }
    }
    return const [];
  }

  List<GeneratedProject> _readProjects(dynamic decoded) {
    return _readList(decoded, const ['projects', 'saved_projects', 'results'])
        .whereType<Map>()
        .map((item) => GeneratedProject.fromJson(Map<String, dynamic>.from(item)))
        .toList();
  }

  String? _extractErrorMessage(dynamic decoded) {
    if (decoded is Map<String, dynamic>) {
      final directMessage = _readMessageFromDecoded(decoded);
      if (directMessage != null && directMessage.isNotEmpty) {
        return directMessage;
      }

      final detail = decoded['detail'];
      if (detail is List && detail.isNotEmpty) {
        return detail.first.toString();
      }
      if (detail != null) {
        final message = detail.toString().trim();
        if (message.isNotEmpty) {
          return message;
        }
      }
    }
    return null;
  }

  String? _readMessageFromDecoded(Map<String, dynamic> decoded) {
    final keys = ['message', 'detail', 'error'];
    for (final key in keys) {
      final value = decoded[key];
      if (value == null) {
        continue;
      }
      final text = value.toString().trim();
      if (text.isNotEmpty) {
        return text;
      }
    }
    return null;
  }

  bool _isOfflineMessage(String message) {
    return message.contains('xmlhttprequest') ||
        message.contains('connection refused') ||
        message.contains('failed host lookup') ||
        message.contains('network') ||
        message.contains('socketexception');
  }
}

class ApiException implements Exception {
  const ApiException(this.message);

  final String message;

  @override
  String toString() => message;
}
