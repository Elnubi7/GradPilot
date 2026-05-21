import 'package:flutter/material.dart';

import '../core/app_colors.dart';
import '../models/app_user.dart';
import 'glass_card.dart';

class UserTableCard extends StatelessWidget {
  const UserTableCard({
    super.key,
    required this.users,
    required this.onEdit,
    required this.onDelete,
  });

  final List<AppUser> users;
  final void Function(AppUser user) onEdit;
  final void Function(AppUser user) onDelete;

  @override
  Widget build(BuildContext context) {
    return GlassCard(
      padding: const EdgeInsets.all(12),
      borderRadius: 22,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: DataTable(
          columnSpacing: 26,
          headingTextStyle: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: AppColors.textPrimary,
                fontWeight: FontWeight.w800,
              ),
          dataTextStyle: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: AppColors.textSecondary,
              ),
          columns: const [
            DataColumn(label: Text('Name')),
            DataColumn(label: Text('Email')),
            DataColumn(label: Text('Phone')),
            DataColumn(label: Text('Department')),
            DataColumn(label: Text('Actions')),
          ],
          rows: users.map((user) {
            return DataRow(
              cells: [
                DataCell(Text(user.fullName)),
                DataCell(Text(user.email)),
                DataCell(Text(user.phone)),
                DataCell(Text(user.department)),
                DataCell(
                  Row(
                    children: [
                      IconButton(
                        tooltip: 'Edit user',
                        icon: const Icon(Icons.edit_outlined),
                        onPressed: () => onEdit(user),
                      ),
                      IconButton(
                        tooltip: 'Delete user',
                        icon: const Icon(Icons.delete_outline_rounded),
                        onPressed: () => onDelete(user),
                      ),
                    ],
                  ),
                ),
              ],
            );
          }).toList(),
        ),
      ),
    );
  }
}
