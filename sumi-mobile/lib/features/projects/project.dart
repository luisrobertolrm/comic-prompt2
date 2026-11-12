import '../library/character.dart';
import '../production/scenario.dart';

class Project {
  final String id;
  final String title;
  final String subtitle;
  final String genre;
  final String tone;
  final String status;
  final int pages;
  final String style;
  final String colorMode;
  final String coverAccent;
  final String coverTone;
  final String? narratorVoiceId;
  final String? videoUrl;
  final double synopsisTemperature;
  final double panelsTemperature;
  final DateTime updatedAt;

  final String? premise;
  final String? synopsis;
  final List<Character> characters;
  final List<Scenario> scenarios;

  const Project({
    required this.id,
    required this.title,
    required this.subtitle,
    required this.genre,
    required this.tone,
    required this.status,
    required this.pages,
    required this.style,
    required this.colorMode,
    required this.coverAccent,
    required this.coverTone,
    required this.updatedAt,
    this.narratorVoiceId,
    this.videoUrl,
    this.synopsisTemperature = 0.7,
    this.panelsTemperature = 0.7,
    this.premise,
    this.synopsis,
    this.characters = const [],
    this.scenarios = const [],
  });

  factory Project.fromJson(Map<String, dynamic> j) => Project(
        id: j['id'].toString(),
        title: j['title'] as String? ?? '',
        subtitle: j['subtitle'] as String? ?? '',
        genre: j['genre'] as String? ?? '',
        tone: j['tone'] as String? ?? '',
        status: j['status'] as String? ?? '',
        pages: j['pages'] as int? ?? 4,
        style: j['style'] as String? ?? '',
        colorMode: j['color_mode'] as String? ?? '',
        coverAccent: j['cover_accent'] as String? ?? 'accent',
        coverTone: j['cover_tone'] as String? ?? 'dots',
        narratorVoiceId: j['narrator_voice_id']?.toString(),
        videoUrl: j['video_url'] as String?,
        synopsisTemperature: (j['synopsis_temperature'] as num?)?.toDouble() ?? 0.7,
        panelsTemperature: (j['panels_temperature'] as num?)?.toDouble() ?? 0.7,
        updatedAt: DateTime.tryParse(j['updated_at'] as String? ?? '') ?? DateTime.now(),
        premise: j['premise'] as String?,
        synopsis: j['synopsis'] as String?,
        characters: (j['characters'] as List? ?? const [])
            .map((e) => Character.fromJson((e as Map).cast<String, dynamic>()))
            .toList(),
        scenarios: (j['scenarios'] as List? ?? const [])
            .map((e) => Scenario.fromJson((e as Map).cast<String, dynamic>()))
            .toList(),
      );
}
