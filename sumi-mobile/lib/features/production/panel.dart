const bubbleKinds = ['say', 'thought', 'shout', 'whisper', 'narration'];
const bubbleKindLabels = {
  'say': 'Fala',
  'thought': 'Pensamento',
  'shout': 'Grito',
  'whisper': 'Sussurro',
  'narration': 'Narração',
};

class Bubble {
  final String text;
  final String kind;
  final String side;
  final String tail;
  final int x;
  final int y;

  const Bubble({
    required this.text,
    this.kind = 'say',
    this.side = 'left',
    this.tail = 'none',
    this.x = 8,
    this.y = 12,
  });

  factory Bubble.fromJson(Map<String, dynamic> j) => Bubble(
        text: j['text'] as String? ?? '',
        kind: j['kind'] as String? ?? 'say',
        side: j['side'] as String? ?? 'left',
        tail: j['tail'] as String? ?? 'none',
        x: (j['x'] as num?)?.round() ?? 8,
        y: (j['y'] as num?)?.round() ?? 12,
      );

  Map<String, dynamic> toJson() =>
      {'text': text, 'kind': kind, 'side': side, 'tail': tail, 'x': x, 'y': y};

  Bubble copyWith({String? text, String? kind, String? side, String? tail, int? x, int? y}) =>
      Bubble(
        text: text ?? this.text,
        kind: kind ?? this.kind,
        side: side ?? this.side,
        tail: tail ?? this.tail,
        x: x ?? this.x,
        y: y ?? this.y,
      );
}

class Panel {
  final String id;
  final String projectId;
  final int indexOrder;
  final String label;
  final String aspect;
  final String tone;
  final String? characterName;
  final String caption;
  final String framing;
  final String prompt;
  final String status;
  final List<Bubble> bubbles;
  final String? imageUrl;
  final int? synopsisStart;
  final int? synopsisEnd;

  const Panel({
    required this.id,
    required this.projectId,
    required this.indexOrder,
    required this.label,
    this.aspect = '4-3',
    this.tone = 'dots',
    this.characterName,
    this.caption = '',
    this.framing = 'Plano médio',
    this.prompt = '',
    this.status = 'pending',
    this.bubbles = const [],
    this.imageUrl,
    this.synopsisStart,
    this.synopsisEnd,
  });

  bool get hasImage => imageUrl != null && imageUrl!.isNotEmpty;

  factory Panel.fromJson(Map<String, dynamic> j) => Panel(
        id: j['id'].toString(),
        projectId: j['project_id'].toString(),
        indexOrder: j['index_order'] as int? ?? 0,
        label: j['label'] as String? ?? '',
        aspect: j['aspect'] as String? ?? '4-3',
        tone: j['tone'] as String? ?? 'dots',
        characterName: j['character_name'] as String?,
        caption: j['caption'] as String? ?? '',
        framing: j['framing'] as String? ?? 'Plano médio',
        prompt: j['prompt'] as String? ?? '',
        status: j['status'] as String? ?? 'pending',
        bubbles: (j['bubbles'] as List? ?? const [])
            .map((e) => Bubble.fromJson((e as Map).cast<String, dynamic>()))
            .toList(),
        imageUrl: j['image_url'] as String?,
        synopsisStart: j['synopsis_start'] as int?,
        synopsisEnd: j['synopsis_end'] as int?,
      );

  Panel copyWith({List<Bubble>? bubbles, String? caption, String? label, String? framing}) =>
      Panel(
        id: id,
        projectId: projectId,
        indexOrder: indexOrder,
        label: label ?? this.label,
        aspect: aspect,
        tone: tone,
        characterName: characterName,
        caption: caption ?? this.caption,
        framing: framing ?? this.framing,
        prompt: prompt,
        status: status,
        bubbles: bubbles ?? this.bubbles,
        imageUrl: imageUrl,
        synopsisStart: synopsisStart,
        synopsisEnd: synopsisEnd,
      );
}
