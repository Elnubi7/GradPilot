class AppUser {
  const AppUser({
    required this.id,
    required this.fullName,
    required this.email,
    required this.phone,
    required this.department,
    required this.avatarStyle,
    this.password,
    this.createdAt,
  });

  final String? id;
  final String fullName;
  final String email;
  final String phone;
  final String department;
  final String? password;
  final String avatarStyle;
  final String? createdAt;

  AppUser copyWith({
    String? id,
    String? fullName,
    String? email,
    String? phone,
    String? department,
    String? password,
    String? avatarStyle,
    String? createdAt,
    bool clearPassword = false,
  }) {
    return AppUser(
      id: id ?? this.id,
      fullName: fullName ?? this.fullName,
      email: email ?? this.email,
      phone: phone ?? this.phone,
      department: department ?? this.department,
      password: clearPassword ? null : (password ?? this.password),
      avatarStyle: avatarStyle ?? this.avatarStyle,
      createdAt: createdAt ?? this.createdAt,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'fullName': fullName,
        'email': email,
        'phone': phone,
        'department': department,
        'password': password,
        'avatarStyle': avatarStyle,
        'createdAt': createdAt,
      };

  Map<String, dynamic> toRegisterJson() => {
        'full_name': fullName,
        'email': email,
        'phone': phone,
        'department': department,
        'password': password,
        'avatar_style': avatarStyle,
      };

  factory AppUser.fromJson(Map<String, dynamic> json) {
    return AppUser(
      id: _readNullableString(json, const ['id']),
      fullName: _readString(
        json,
        const ['fullName', 'full_name'],
        fallback: '',
      ),
      email: _readString(json, const ['email'], fallback: ''),
      phone: _readString(json, const ['phone'], fallback: ''),
      department: _readString(
        json,
        const ['department'],
        fallback: '',
      ),
      password: _readNullableString(json, const ['password']),
      avatarStyle: _readString(
        json,
        const ['avatarStyle', 'avatar_style'],
        fallback: 'blue',
      ),
      createdAt: _readNullableString(
        json,
        const ['createdAt', 'created_at'],
      ),
    );
  }

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

  static String? _readNullableString(
    Map<String, dynamic> json,
    List<String> keys,
  ) {
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
    return null;
  }
}
