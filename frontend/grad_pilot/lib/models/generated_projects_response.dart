import 'generated_project.dart';

class GeneratedProjectsResponse {
  const GeneratedProjectsResponse({
    required this.generatedProjects,
    required this.papersFound,
    required this.repositoriesFound,
    required this.message,
    required this.parsedPreferences,
  });

  final List<GeneratedProject> generatedProjects;
  final int papersFound;
  final int repositoriesFound;
  final String message;
  final Map<String, dynamic> parsedPreferences;

  bool get hasRateLimitWarning {
    final normalized = message.toLowerCase();
    return normalized.contains('arxiv rate limited') ||
        normalized.contains('rate limited') ||
        normalized.contains('try again later');
  }

  factory GeneratedProjectsResponse.fromJson(Map<String, dynamic> json) {
    final rawProjects = json['generated_projects'];
    final projects = rawProjects is List
        ? rawProjects
            .whereType<Map>()
            .map(
              (item) => GeneratedProject.fromJson(
                Map<String, dynamic>.from(item),
              ),
            )
            .toList()
        : <GeneratedProject>[];

    return GeneratedProjectsResponse(
      generatedProjects: projects,
      papersFound: _readInt(json['papers_found']),
      repositoriesFound: _readInt(json['repositories_found']),
      message: (json['message']?.toString().trim().isNotEmpty ?? false)
          ? json['message'].toString().trim()
          : 'Here are your generated source-backed ideas.',
      parsedPreferences: json['parsed_preferences'] is Map
          ? Map<String, dynamic>.from(json['parsed_preferences'] as Map)
          : <String, dynamic>{},
    );
  }

  static int _readInt(dynamic value) {
    if (value is int) {
      return value;
    }
    if (value is num) {
      return value.toInt();
    }
    if (value is String) {
      return int.tryParse(value.trim()) ?? 0;
    }
    return 0;
  }
}
