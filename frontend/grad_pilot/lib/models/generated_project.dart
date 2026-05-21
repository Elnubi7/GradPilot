class GeneratedProject {
  const GeneratedProject({
    required this.id,
    required this.title,
    required this.category,
    required this.difficulty,
    required this.durationMonths,
    required this.techStack,
    required this.description,
    required this.problem,
    required this.solution,
    required this.features,
    required this.evaluationMetrics,
    required this.paperLink,
    required this.githubLink,
    required this.feasibilityScore,
    required this.scope,
    required this.architectureSummary,
    required this.weeklyMilestones,
    required this.risks,
    required this.sourceStatus,
    required this.sourceTitles,
    required this.sourceQualityScore,
    required this.paperScore,
    required this.repositoryScore,
  });

  final String id;
  final String title;
  final String category;
  final String difficulty;
  final int? durationMonths;
  final List<String> techStack;
  final String description;
  final String problem;
  final String solution;
  final List<String> features;
  final List<String> evaluationMetrics;
  final String paperLink;
  final String githubLink;
  final double? feasibilityScore;
  final String scope;
  final String architectureSummary;
  final List<String> weeklyMilestones;
  final List<String> risks;
  final String sourceStatus;
  final List<String> sourceTitles;
  final double? sourceQualityScore;
  final double? paperScore;
  final double? repositoryScore;

  factory GeneratedProject.fromJson(Map<String, dynamic> json) {
    final title = _readString(
      json,
      const ['title', 'project_title', 'name'],
      fallback: 'Untitled Project',
    );

    return GeneratedProject(
      id: _readString(
        json,
        const ['id', 'project_id'],
        fallback: title,
      ),
      title: title,
      category: _readString(
        json,
        const ['category', 'domain', 'project_type'],
        fallback: 'AI Project',
      ),
      difficulty: _readString(
        json,
        const ['difficulty', 'level'],
        fallback: 'Intermediate',
      ),
      durationMonths: _readInt(json, const ['durationMonths', 'duration_months']),
      techStack: _readStringList(
        json,
        const ['techStack', 'tech_stack', 'preferred_stack'],
      ),
      description: _readString(
        json,
        const ['description', 'summary'],
        fallback: 'No description provided.',
      ),
      problem: _readString(json, const ['problem'], fallback: ''),
      solution: _readString(json, const ['solution'], fallback: ''),
      features: _readStringList(json, const ['features']),
      evaluationMetrics: _readStringList(
        json,
        const ['evaluationMetrics', 'evaluation_metrics'],
      ),
      paperLink: _readString(json, const ['paperLink', 'paper_link']),
      githubLink: _readString(json, const ['githubLink', 'github_link']),
      feasibilityScore: _readDouble(
        json,
        const ['feasibilityScore', 'feasibility_score'],
      ),
      scope: _readString(json, const ['scope'], fallback: ''),
      architectureSummary: _readString(
        json,
        const ['architectureSummary', 'architecture_summary'],
        fallback: '',
      ),
      weeklyMilestones: _readStringList(
        json,
        const ['weeklyMilestones', 'weekly_milestones'],
      ),
      risks: _readStringList(json, const ['risks']),
      sourceStatus: _readString(
        json,
        const ['sourceStatus', 'source_status'],
        fallback: 'unknown',
      ),
      sourceTitles: _readStringList(json, const ['sourceTitles', 'source_titles']),
      sourceQualityScore: _readDouble(
        json,
        const ['sourceQualityScore', 'source_quality_score'],
      ),
      paperScore: _readDouble(json, const ['paperScore', 'paper_score']),
      repositoryScore: _readDouble(
        json,
        const ['repositoryScore', 'repository_score'],
      ),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'category': category,
        'difficulty': difficulty,
        'duration_months': durationMonths,
        'tech_stack': techStack,
        'description': description,
        'problem': problem,
        'solution': solution,
        'features': features,
        'evaluation_metrics': evaluationMetrics,
        'paper_link': paperLink.isEmpty ? null : paperLink,
        'github_link': githubLink.isEmpty ? null : githubLink,
        'feasibility_score': feasibilityScore,
        'scope': scope,
        'architecture_summary': architectureSummary,
        'weekly_milestones': weeklyMilestones,
        'risks': risks,
        'source_status': sourceStatus,
        'source_titles': sourceTitles,
        'source_quality_score': sourceQualityScore,
        'paper_score': paperScore,
        'repository_score': repositoryScore,
      };

  static String _readString(
    Map<String, dynamic> json,
    List<String> keys, {
    String fallback = '',
  }) {
    for (final key in keys) {
      final value = json[key];
      if (value == null) {
        continue;
      }
      final text = value.toString().trim();
      if (text.isNotEmpty) {
        return text;
      }
    }
    return fallback;
  }

  static List<String> _readStringList(
    Map<String, dynamic> json,
    List<String> keys,
  ) {
    for (final key in keys) {
      final value = json[key];
      if (value is List) {
        return value
            .map((item) => item.toString().trim())
            .where((item) => item.isNotEmpty)
            .toList();
      }
      if (value is String && value.trim().isNotEmpty) {
        return value
            .split(',')
            .map((item) => item.trim())
            .where((item) => item.isNotEmpty)
            .toList();
      }
    }
    return const [];
  }

  static int? _readInt(Map<String, dynamic> json, List<String> keys) {
    for (final key in keys) {
      final value = json[key];
      if (value is int) {
        return value;
      }
      if (value is num) {
        return value.toInt();
      }
      if (value is String) {
        return int.tryParse(value.trim());
      }
    }
    return null;
  }

  static double? _readDouble(Map<String, dynamic> json, List<String> keys) {
    for (final key in keys) {
      final value = json[key];
      if (value is double) {
        return value;
      }
      if (value is num) {
        return value.toDouble();
      }
      if (value is String) {
        return double.tryParse(value.trim());
      }
    }
    return null;
  }
}
