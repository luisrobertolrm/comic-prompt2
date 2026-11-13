class Scenario {
  final String id;
  final String name;
  final String kind;
  final String? summary;
  final String? locationType;
  final String? timeOfDay;
  final String? weather;
  final String? atmosphere;
  final String? details;
  final String style;
  final bool approved;
  final String? imageUrl;
  final int projectCount;

  const Scenario({
    required this.id,
    required this.name,
    this.kind = '',
    this.summary,
    this.locationType,
    this.timeOfDay,
    this.weather,
    this.atmosphere,
    this.details,
    this.style = '',
    this.approved = false,
    this.imageUrl,
    this.projectCount = 0,
  });

  factory Scenario.fromJson(Map<String, dynamic> j) => Scenario(
        id: j['id'].toString(),
        name: j['name'] as String? ?? '',
        kind: j['kind'] as String? ?? '',
        summary: j['summary'] as String?,
        locationType: j['location_type'] as String?,
        timeOfDay: j['time_of_day'] as String?,
        weather: j['weather'] as String?,
        atmosphere: j['atmosphere'] as String?,
        details: j['details'] as String?,
        style: j['style'] as String? ?? '',
        approved: j['approved'] as bool? ?? false,
        imageUrl: j['image_url'] as String?,
        projectCount: j['project_count'] as int? ?? 0,
      );

  String get initial => name.isEmpty ? '?' : name.substring(0, 1).toUpperCase();
}

/// Resposta de `POST /scenarios/ai-draft`: a intenção reconhecida e, quando é
/// um cenário, o rascunho para revisar no formulário.
class ScenarioAiResult {
  final String intent;
  final String message;
  final Scenario? draft;

  const ScenarioAiResult({required this.intent, this.message = '', this.draft});

  bool get isScenario => intent == 'preencher_cenario' && draft != null;

  factory ScenarioAiResult.fromJson(Map<String, dynamic> j) {
    final s = j['scenario'] as Map?;
    return ScenarioAiResult(
      intent: j['intent'] as String? ?? '',
      message: j['message'] as String? ?? '',
      draft: s == null ? null : Scenario.fromJson({...s.cast<String, dynamic>(), 'id': ''}),
    );
  }
}
