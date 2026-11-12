/// Grupo de atributos de `/character-options` e `/scenario-options`.
class AttrGroup {
  final String id;
  final String label;
  final bool multi;
  final List<AttrOption> options;
  const AttrGroup(this.id, this.label, this.multi, this.options);

  factory AttrGroup.fromJson(Map<String, dynamic> j) => AttrGroup(
        j['id'].toString(),
        j['label'] as String? ?? '',
        j['multi'] as bool? ?? false,
        (j['options'] as List? ?? const [])
            .map((e) => AttrOption.fromJson((e as Map).cast<String, dynamic>()))
            .toList(),
      );

  String labelOf(String? optionId) =>
      options.where((o) => o.id == optionId).map((o) => o.label).firstOrNull ?? '';
}

class AttrOption {
  final String id;
  final String label;
  const AttrOption(this.id, this.label);

  factory AttrOption.fromJson(Map<String, dynamic> j) =>
      AttrOption(j['id'].toString(), j['label'] as String? ?? '');
}

class ImageCandidate {
  final String id;
  final String url;
  final String notes;
  const ImageCandidate(this.id, this.url, this.notes);

  factory ImageCandidate.fromJson(Map<String, dynamic> j) =>
      ImageCandidate(j['id'].toString(), j['url'] as String? ?? '', j['notes'] as String? ?? '');
}

/// Estado comum dos jobs assíncronos: `pending | running | done | error`.
class Job {
  final String jobId;
  final String status;
  final String detail;
  final int progress;
  final List<ImageCandidate> candidates;
  final String? videoUrl;

  const Job({
    required this.jobId,
    required this.status,
    this.detail = '',
    this.progress = 0,
    this.candidates = const [],
    this.videoUrl,
  });

  bool get isFinished => status == 'done' || status == 'error';
  bool get isError => status == 'error';

  /// `portraits` (retrato), `scenes` (cenário) ou `video_url` (vídeo).
  factory Job.fromJson(Map<String, dynamic> j) => Job(
        jobId: j['job_id'].toString(),
        status: j['status'] as String? ?? 'pending',
        detail: j['detail'] as String? ?? '',
        progress: j['progress'] as int? ?? 0,
        candidates: ((j['portraits'] ?? j['scenes']) as List? ?? const [])
            .map((e) => ImageCandidate.fromJson((e as Map).cast<String, dynamic>()))
            .toList(),
        videoUrl: j['video_url'] as String?,
      );
}
