import 'app_user.dart';

class AuthResponse {
  const AuthResponse({
    required this.success,
    required this.message,
    this.user,
  });

  final bool success;
  final String message;
  final AppUser? user;

  factory AuthResponse.fromJson(Map<String, dynamic> json) {
    final rawUser = json['user'];

    return AuthResponse(
      success: _readBool(json['success']),
      message: _readMessage(json),
      user: rawUser is Map
          ? AppUser.fromJson(Map<String, dynamic>.from(rawUser))
          : null,
    );
  }

  static bool _readBool(dynamic value) {
    if (value is bool) {
      return value;
    }
    if (value is String) {
      return value.toLowerCase() == 'true';
    }
    return false;
  }

  static String _readMessage(Map<String, dynamic> json) {
    final message = json['message']?.toString().trim();
    if (message != null && message.isNotEmpty) {
      return message;
    }
    return 'Login failed';
  }
}
