class Series {
  final String id;
  final String name;
  final String? description;
  final List<String> projectIds;
  final DateTime updatedAt;

  const Series({
    required this.id,
    required this.name,
    this.description,
    this.projectIds = const [],
    required this.updatedAt,
  });

  factory Series.fromJson(Map<String, dynamic> j) => Series(
        id: j['id'].toString(),
        name: j['name'] as String? ?? '',
        description: j['description'] as String?,
        projectIds: (j['project_ids'] as List? ?? const []).map((e) => e.toString()).toList(),
        updatedAt: DateTime.tryParse(j['updated_at'] as String? ?? '') ?? DateTime.now(),
      );
}
