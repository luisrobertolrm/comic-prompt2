class AppUser {
  final String id;
  final String name;
  final String? email;
  final String plan;
  final String group;
  final bool approved;

  const AppUser({
    required this.id,
    required this.name,
    required this.email,
    required this.plan,
    required this.group,
    required this.approved,
  });

  factory AppUser.fromJson(Map<String, dynamic> j) => AppUser(
        id: j['id'].toString(),
        name: j['name'] as String? ?? '',
        email: j['email'] as String?,
        plan: j['plan'] as String? ?? 'Plano criador',
        group: j['group'] as String? ?? '',
        approved: j['approved'] as bool? ?? true,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'email': email,
        'plan': plan,
        'group': group,
        'approved': approved,
      };

  String get initial => name.isEmpty ? 'U' : name.substring(0, 1).toUpperCase();
}
