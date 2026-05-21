import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../models/app_user.dart';
import '../services/api_service.dart';
import '../widgets/app_button.dart';
import '../widgets/app_text_field.dart';
import '../widgets/empty_state.dart';
import '../widgets/loading_view.dart';
import '../widgets/stat_card.dart';
import '../widgets/user_table_card.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final _apiService = const ApiService();

  List<AppUser> _users = <AppUser>[];
  bool _isLoading = true;
  String? _errorMessage;

  int get _departmentCount =>
      _users.map((user) => user.department.trim().toLowerCase()).toSet().length;

  @override
  void initState() {
    super.initState();
    _loadUsers();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Users Dashboard'),
        backgroundColor: Colors.transparent,
        actions: [
          Padding(
            padding: const EdgeInsetsDirectional.only(end: 12),
            child: IconButton.filled(
              tooltip: 'Add user',
              onPressed: () => _showUserForm(),
              icon: const Icon(Icons.person_add_alt_rounded),
            ),
          ),
        ],
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
          title: 'Loading Users',
          lines: ['Fetching dashboard records...'],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadUsers,
      child: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 900),
          child: ListView(
            padding: const EdgeInsets.all(24),
            children: [
              LayoutBuilder(
                builder: (context, constraints) {
                  final stats = [
                    StatCard(
                      label: 'Total Users',
                      value: _users.length.toString(),
                      icon: Icons.people_alt_outlined,
                    ),
                    StatCard(
                      label: 'Departments',
                      value: _departmentCount.toString(),
                      icon: Icons.apartment_rounded,
                    ),
                    const StatCard(
                      label: 'Active User',
                      value: '1',
                      icon: Icons.verified_user_outlined,
                    ),
                  ];

                  if (constraints.maxWidth < 700) {
                    return Column(
                      children: stats
                          .map(
                            (stat) => Padding(
                              padding: const EdgeInsets.only(bottom: 12),
                              child: stat,
                            ),
                          )
                          .toList(),
                    );
                  }

                  return Row(
                    children: [
                      for (var index = 0; index < stats.length; index++) ...[
                        Expanded(child: stats[index]),
                        if (index != stats.length - 1)
                          const SizedBox(width: 12),
                      ],
                    ],
                  );
                },
              ),
              const SizedBox(height: 18),
              AppButton(
                label: 'Add User',
                icon: Icons.person_add_alt_rounded,
                onPressed: () => _showUserForm(),
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
              const SizedBox(height: 18),
              if (_users.isEmpty)
                const EmptyState(
                  title: 'No users found.',
                  message: 'Add a user to start building the dashboard.',
                  icon: Icons.people_outline_rounded,
                )
              else
                LayoutBuilder(
                  builder: (context, constraints) {
                    if (constraints.maxWidth >= 720) {
                      return UserTableCard(
                        users: _users,
                        onEdit: (user) => _showUserForm(user: user),
                        onDelete: _confirmDeleteUser,
                      );
                    }

                    return Column(
                      children: _users.map((user) {
                        return Padding(
                          padding: const EdgeInsets.only(bottom: 12),
                          child: _UserMobileCard(
                            user: user,
                            onEdit: () => _showUserForm(user: user),
                            onDelete: () => _confirmDeleteUser(user),
                          ),
                        );
                      }).toList(),
                    );
                  },
                ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _loadUsers() async {
    try {
      final users = await _apiService.getUsers();
      if (!mounted) {
        return;
      }
      setState(() {
        _users = users;
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

  Future<void> _showUserForm({AppUser? user}) async {
    final result = await showModalBottomSheet<AppUser>(
      context: context,
      isScrollControlled: true,
      backgroundColor: AppColors.background,
      builder: (context) => _UserFormSheet(
        user: user,
        onSubmit: (payload) {
          if (user == null) {
            return _apiService.register(
              fullName: payload.fullName,
              email: payload.email,
              phone: payload.phone,
              department: payload.department,
              password: payload.password ?? '',
              avatarStyle: payload.avatarStyle,
            );
          }

          final body = {
            'full_name': payload.fullName,
            'email': payload.email,
            'phone': payload.phone,
            'department': payload.department,
            'avatar_style': payload.avatarStyle,
            if (payload.password?.isNotEmpty ?? false)
              'password': payload.password,
          };
          return _apiService.updateUser(user.id ?? '', body);
        },
      ),
    );

    if (result == null || !mounted) {
      return;
    }

    await _loadUsers();
    _showSnack(user == null ? 'User added.' : 'User updated.');
  }

  Future<void> _confirmDeleteUser(AppUser user) async {
    final id = user.id;
    if (id == null || id.isEmpty) {
      _showSnack('This user cannot be deleted because it has no id.');
      return;
    }

    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Delete user?'),
        content: Text('Remove ${user.fullName} from the dashboard.'),
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
      await _apiService.deleteUser(id);
      if (!mounted) {
        return;
      }
      setState(() {
        _users.removeWhere((item) => item.id == id);
      });
      _showSnack('User deleted.');
    } on ApiException catch (error) {
      _showSnack(error.message);
    }
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

class _UserFormSheet extends StatefulWidget {
  const _UserFormSheet({
    required this.user,
    required this.onSubmit,
  });

  final AppUser? user;
  final Future<AppUser> Function(_UserPayload payload) onSubmit;

  @override
  State<_UserFormSheet> createState() => _UserFormSheetState();
}

class _UserFormSheetState extends State<_UserFormSheet> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nameController;
  late final TextEditingController _emailController;
  late final TextEditingController _phoneController;
  late final TextEditingController _departmentController;
  late final TextEditingController _passwordController;
  late final TextEditingController _avatarStyleController;

  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    final user = widget.user;
    _nameController = TextEditingController(text: user?.fullName ?? '');
    _emailController = TextEditingController(text: user?.email ?? '');
    _phoneController = TextEditingController(text: user?.phone ?? '');
    _departmentController = TextEditingController(text: user?.department ?? '');
    _passwordController = TextEditingController();
    _avatarStyleController =
        TextEditingController(text: user?.avatarStyle ?? 'blue');
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _departmentController.dispose();
    _passwordController.dispose();
    _avatarStyleController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isEdit = widget.user != null;

    return SafeArea(
      child: SingleChildScrollView(
        padding: EdgeInsets.fromLTRB(
          24,
          24,
          24,
          24 + MediaQuery.of(context).viewInsets.bottom,
        ),
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              AppTextField(
                label: 'Full Name',
                hint: 'Student name',
                controller: _nameController,
                prefixIcon: Icons.person_outline_rounded,
                validator: _validateName,
              ),
              const SizedBox(height: 14),
              AppTextField(
                label: 'Email',
                hint: 'student@example.com',
                controller: _emailController,
                prefixIcon: Icons.email_outlined,
                keyboardType: TextInputType.emailAddress,
                validator: _validateEmail,
              ),
              const SizedBox(height: 14),
              AppTextField(
                label: 'Phone',
                hint: '01012345678',
                controller: _phoneController,
                prefixIcon: Icons.phone_outlined,
                keyboardType: TextInputType.phone,
                validator: _validateEgyptianPhone,
              ),
              const SizedBox(height: 14),
              AppTextField(
                label: 'Department',
                hint: 'Computer Science',
                controller: _departmentController,
                prefixIcon: Icons.apartment_rounded,
                validator: _validateRequired,
              ),
              const SizedBox(height: 14),
              AppTextField(
                label: isEdit ? 'Password (optional)' : 'Password',
                hint: isEdit ? 'Leave blank to keep current password' : 'At least 6 chars, letter and number',
                controller: _passwordController,
                prefixIcon: Icons.lock_outline_rounded,
                obscureText: true,
                validator: isEdit ? _validateOptionalPassword : _validatePassword,
              ),
              const SizedBox(height: 14),
              AppTextField(
                label: 'Avatar Style',
                hint: 'blue',
                controller: _avatarStyleController,
                prefixIcon: Icons.palette_outlined,
                validator: _validateRequired,
              ),
              const SizedBox(height: 18),
              AppButton(
                label: isEdit ? 'Update User' : 'Add User',
                icon: isEdit ? Icons.save_outlined : Icons.person_add_alt_rounded,
                isLoading: _isSaving,
                onPressed: _isSaving ? null : _submit,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) {
      return;
    }

    setState(() {
      _isSaving = true;
    });

    try {
      final user = await widget.onSubmit(
        _UserPayload(
          fullName: _nameController.text.trim(),
          email: _emailController.text.trim().toLowerCase(),
          phone: _phoneController.text.trim(),
          department: _departmentController.text.trim(),
          password: _passwordController.text.trim().isEmpty
              ? null
              : _passwordController.text.trim(),
          avatarStyle: _avatarStyleController.text.trim().isEmpty
              ? 'blue'
              : _avatarStyleController.text.trim(),
        ),
      );
      if (context.mounted) {
        Navigator.of(context).pop(user);
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
  }

  String? _validateName(String? value) {
    final text = value?.trim() ?? '';
    if (text.length < 3) {
      return 'Name must be at least 3 characters.';
    }
    if (RegExp(r'\d').hasMatch(text)) {
      return 'Name cannot contain numbers.';
    }
    return null;
  }

  String? _validateEmail(String? value) {
    final text = value?.trim() ?? '';
    if (!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$').hasMatch(text)) {
      return 'Enter a valid email.';
    }
    return null;
  }

  String? _validateEgyptianPhone(String? value) {
    final text = value?.trim() ?? '';
    if (!RegExp(r'^(010|011|012|015)\d{8}$').hasMatch(text)) {
      return 'Enter a valid Egyptian phone number.';
    }
    return null;
  }

  String? _validateRequired(String? value) {
    if (value?.trim().isEmpty ?? true) {
      return 'This field is required.';
    }
    return null;
  }

  String? _validatePassword(String? value) {
    final text = value?.trim() ?? '';
    if (text.length < 6 ||
        !RegExp('[A-Za-z]').hasMatch(text) ||
        !RegExp(r'\d').hasMatch(text)) {
      return 'Password must include 6 chars, a letter, and a number.';
    }
    return null;
  }

  String? _validateOptionalPassword(String? value) {
    final text = value?.trim() ?? '';
    if (text.isEmpty) {
      return null;
    }
    return _validatePassword(value);
  }
}

class _UserPayload {
  const _UserPayload({
    required this.fullName,
    required this.email,
    required this.phone,
    required this.department,
    required this.password,
    required this.avatarStyle,
  });

  final String fullName;
  final String email;
  final String phone;
  final String department;
  final String? password;
  final String avatarStyle;
}

class _UserMobileCard extends StatelessWidget {
  const _UserMobileCard({
    required this.user,
    required this.onEdit,
    required this.onDelete,
  });

  final AppUser user;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  @override
  Widget build(BuildContext context) {
    return Card(
      color: AppColors.card.withValues(alpha: 0.65),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(18),
        side: const BorderSide(color: AppColors.border),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              user.fullName,
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                    color: AppColors.textPrimary,
                    fontWeight: FontWeight.w800,
                  ),
            ),
            const SizedBox(height: 6),
            Text(user.email),
            Text(user.phone),
            Text(user.department),
            const SizedBox(height: 10),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                IconButton(
                  tooltip: 'Edit user',
                  onPressed: onEdit,
                  icon: const Icon(Icons.edit_outlined),
                ),
                IconButton(
                  tooltip: 'Delete user',
                  onPressed: onDelete,
                  icon: const Icon(Icons.delete_outline_rounded),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
