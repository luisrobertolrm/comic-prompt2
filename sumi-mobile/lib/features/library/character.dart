class Character {
  final String id;
  final String name;
  final String role;
  final String? gender;
  final String? bodyType;
  final String? skinTone;
  final String? ethnicity;
  final int? age;
  final String? height;
  final String? summary;
  final String? outfit;
  final List<String> traits;
  final String style;
  final bool approved;
  final String? imageUrl;
  final String? narratorVoiceId;
  final int projectCount;

  const Character({
    required this.id,
    required this.name,
    required this.role,
    this.gender,
    this.bodyType,
    this.skinTone,
    this.ethnicity,
    this.age,
    this.height,
    this.summary,
    this.outfit,
    this.traits = const [],
    this.style = '',
    this.approved = false,
    this.imageUrl,
    this.narratorVoiceId,
    this.projectCount = 0,
  });

  factory Character.fromJson(Map<String, dynamic> j) => Character(
        id: j['id'].toString(),
        name: j['name'] as String? ?? '',
        role: j['role'] as String? ?? 'Personagem',
        gender: j['gender'] as String?,
        bodyType: j['body_type'] as String?,
        skinTone: j['skin_tone'] as String?,
        ethnicity: j['ethnicity'] as String?,
        age: j['age'] as int?,
        height: j['height'] as String?,
        summary: j['summary'] as String?,
        outfit: j['outfit'] as String?,
        traits: (j['traits'] as List? ?? const []).map((e) => e.toString()).toList(),
        style: j['style'] as String? ?? '',
        approved: j['approved'] as bool? ?? false,
        imageUrl: j['image_url'] as String?,
        narratorVoiceId: j['narrator_voice_id']?.toString(),
        projectCount: j['project_count'] as int? ?? 0,
      );

  String get initial => name.isEmpty ? '?' : name.substring(0, 1).toUpperCase();
}

/// Resposta de `POST /characters/ai-draft`: a intenção reconhecida e, quando é
/// um personagem, o rascunho para revisar no formulário.
class CharacterAiResult {
  final String intent;
  final String message;
  final Character? draft;

  const CharacterAiResult({required this.intent, this.message = '', this.draft});

  bool get isCharacter => intent == 'preencher_personagem' && draft != null;

  factory CharacterAiResult.fromJson(Map<String, dynamic> j) {
    final c = j['character'] as Map?;
    return CharacterAiResult(
      intent: j['intent'] as String? ?? '',
      message: j['message'] as String? ?? '',
      draft: c == null ? null : Character.fromJson({...c.cast<String, dynamic>(), 'id': ''}),
    );
  }
}
