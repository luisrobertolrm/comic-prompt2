class Voice {
  final String id;
  final String name;
  final String voiceId;
  final int? ageStart;
  final int? ageEnd;
  final String? sex;
  final String? details;

  const Voice({
    required this.id,
    required this.name,
    required this.voiceId,
    this.ageStart,
    this.ageEnd,
    this.sex,
    this.details,
  });

  factory Voice.fromJson(Map<String, dynamic> j) => Voice(
        id: j['id'].toString(),
        name: j['name'] as String? ?? '',
        voiceId: j['voice_id'] as String? ?? '',
        ageStart: j['age_start'] as int?,
        ageEnd: j['age_end'] as int?,
        sex: j['sex'] as String?,
        details: j['details'] as String?,
      );

  /// Igual a `voiceMeta` do web: "Feminino · 5–10 anos".
  String get meta {
    final parts = <String>[];
    if (sex != null && sex!.isNotEmpty) parts.add(sex!);
    if (ageStart != null || ageEnd != null) parts.add('${ageStart ?? '?'}–${ageEnd ?? '?'} anos');
    return parts.join(' · ');
  }
}

class VoiceInput {
  final String name;
  final String voiceId;
  final int? ageStart;
  final int? ageEnd;
  final String? sex;
  final String? details;

  const VoiceInput({
    required this.name,
    required this.voiceId,
    this.ageStart,
    this.ageEnd,
    this.sex,
    this.details,
  });

  Map<String, dynamic> toJson() => {
        'name': name,
        'voice_id': voiceId,
        'age_start': ageStart,
        'age_end': ageEnd,
        'sex': sex,
        'details': details,
      };
}
