import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import '../models/app_user.dart';

class LocalUserStore {
  const LocalUserStore();

  static const _usersKey = 'gradpilot_users';
  static const _currentUserKey = 'gradpilot_current_user';

  AppUser get _demoUser => const AppUser(
        id: 'demo-student',
        fullName: 'Demo Student',
        email: 'student@gradpilot.app',
        phone: '01000000000',
        department: 'Computer Science',
        password: '123456',
        avatarStyle: 'blue',
      );

  Future<List<AppUser>> getUsers() async {
    final prefs = await SharedPreferences.getInstance();
    final rawUsers = prefs.getStringList(_usersKey) ?? <String>[];
    final users = rawUsers
        .map((item) => AppUser.fromJson(jsonDecode(item) as Map<String, dynamic>))
        .toList();

    final hasDemoUser = users.any(
      (user) => _normalizeEmail(user.email) == _normalizeEmail(_demoUser.email),
    );

    if (hasDemoUser) {
      return users;
    }

    final seededUsers = <AppUser>[_demoUser, ...users];
    await saveUsers(seededUsers);
    return seededUsers;
  }

  Future<void> saveUsers(List<AppUser> users) async {
    final prefs = await SharedPreferences.getInstance();
    final payload = users.map((user) => jsonEncode(user.toJson())).toList();
    await prefs.setStringList(_usersKey, payload);
  }

  Future<AppUser?> login(String email, String password) async {
    final normalizedEmail = _normalizeEmail(email);
    final users = await getUsers();

    for (final user in users) {
      if (_normalizeEmail(user.email) == normalizedEmail &&
          user.password == password) {
        return user;
      }
    }

    return null;
  }

  Future<AppUser> register(AppUser user) async {
    if (await emailExists(user.email)) {
      throw StateError('An account already exists for this email.');
    }

    final users = await getUsers();
    final normalizedUser = AppUser(
      id: user.id,
      fullName: user.fullName.trim(),
      email: _normalizeEmail(user.email),
      phone: user.phone.trim(),
      department: user.department.trim(),
      password: user.password ?? '',
      avatarStyle: user.avatarStyle.trim().isEmpty ? 'blue' : user.avatarStyle,
      createdAt: user.createdAt,
    );

    users.add(normalizedUser);
    await saveUsers(users);
    return normalizedUser;
  }

  Future<bool> emailExists(String email) async {
    final normalizedEmail = _normalizeEmail(email);
    final users = await getUsers();
    return users.any((user) => _normalizeEmail(user.email) == normalizedEmail);
  }

  Future<void> saveCurrentUser(AppUser user) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _currentUserKey,
      jsonEncode(user.copyWith(clearPassword: true).toJson()),
    );
  }

  Future<AppUser?> getCurrentUser() async {
    final prefs = await SharedPreferences.getInstance();
    final rawUser = prefs.getString(_currentUserKey);
    if (rawUser == null || rawUser.isEmpty) {
      return null;
    }

    return AppUser.fromJson(jsonDecode(rawUser) as Map<String, dynamic>);
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_currentUserKey);
  }

  String _normalizeEmail(String email) => email.trim().toLowerCase();
}
