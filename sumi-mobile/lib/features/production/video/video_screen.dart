import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:video_player/video_player.dart';

import '../../../core/api/api_client.dart';
import '../../../core/services/file_share_service.dart';
import '../../../core/services/notification_service.dart';
import '../../../core/theme/app_theme.dart';
import '../../../shared/error_retry.dart';
import '../../projects/project.dart';
import '../../projects/projects_repository.dart';
import '../candidate_picker.dart';
import '../poll_job.dart';
import '../production_step.dart';
import '../step_action_bar.dart';
import '../../../shared/dictation_button.dart';

const _ytCategories = {
  '1': 'Filme e Animação',
  '24': 'Entretenimento',
  '27': 'Educação',
  '23': 'Comédia',
  '20': 'Games',
  '28': 'Ciência e Tecnologia',
  '22': 'Pessoas e Blogs',
};
const _privacyLabels = {'private': 'Privado', 'unlisted': 'Não listado', 'public': 'Público'};

class VideoScreen extends ConsumerStatefulWidget {
  final String projectId;
  const VideoScreen({super.key, required this.projectId});

  @override
  ConsumerState<VideoScreen> createState() => _VideoScreenState();
}

class _VideoScreenState extends ConsumerState<VideoScreen> {
  Project? _project;
  Object? _error;
  bool _loading = true;
  bool _rendering = false;
  int _progress = 0;
  String _stage = '';
  String _renderError = '';
  bool _sharing = false;
  String? _videoUrl;
  VideoPlayerController? _player;
  JobPoller? _poller;

  ProjectsRepository get _repo => ref.read(projectsRepositoryProvider);

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _poller?.cancel();
    _player?.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final project = await _repo.get(widget.projectId);
      setState(() => _project = project);
      await _setVideo(project.videoUrl);
    } catch (e) {
      setState(() => _error = e);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _setVideo(String? url) async {
    await _player?.dispose();
    _player = null;
    _videoUrl = url;
    if (url == null || url.isEmpty) return;
    final controller = VideoPlayerController.networkUrl(Uri.parse(fileUrl(url)));
    await controller.initialize();
    if (mounted) setState(() => _player = controller);
  }

  Future<void> _render() async {
    setState(() {
      _rendering = true;
      _progress = 0;
      _stage = '';
      _renderError = '';
    });
    try {
      final job = await _repo.startVideo(widget.projectId);
      _poller?.cancel();
      _poller = JobPoller(
        fetch: () => _repo.videoJob(widget.projectId, job.jobId),
        onUpdate: (j) async {
          if (!mounted) return;
          setState(() {
            _progress = j.progress;
            _stage = j.detail;
          });
          if (!j.isFinished) return;
          setState(() {
            _rendering = false;
            if (j.isError) _renderError = j.detail.isEmpty ? 'Falha ao gerar o vídeo.' : j.detail;
          });
          if (!j.isError) {
            ref.invalidate(furthestStepProvider(widget.projectId));
            await _setVideo(j.videoUrl);
          }
        },
      );
    } catch (e) {
      if (mounted) {
        setState(() {
          _rendering = false;
          _renderError = friendlyError(e);
        });
      }
    }
  }

  Future<void> _share() async {
    final url = _videoUrl;
    if (url == null) return;
    setState(() => _sharing = true);
    try {
      final bytes = await _repo.downloadVideo(url);
      final slug = (_project?.title ?? 'sumi')
          .toLowerCase()
          .replaceAll(RegExp(r'[^a-z0-9]+'), '-')
          .replaceAll(RegExp(r'^-+|-+$'), '');
      await ref
          .read(fileShareServiceProvider)
          .shareBytes(bytes, '${slug.isEmpty ? 'sumi' : slug}.mp4', 'video/mp4');
    } catch (_) {
    } finally {
      if (mounted) setState(() => _sharing = false);
    }
  }

  Future<void> _openYoutube() => showModalBottomSheet(
        context: context,
        isScrollControlled: true,
        useSafeArea: true,
        builder: (_) => _YoutubeSheet(projectId: widget.projectId),
      );

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    if (_error != null) return ErrorRetry(error: _error!, onRetry: _load);
    final player = _player;

    return Column(
      children: [
        Expanded(
          child: ListView(
            padding: const EdgeInsets.all(16),
            children: [
              const PageTitle(
                eyebrow: 'VÍDEO',
                title: 'Sua HQ, narrada cena a cena.',
                lede: 'Cada quadro vira uma cena com narração e vozes por personagem.',
              ),
              const SizedBox(height: 16),
              if (player != null && player.value.isInitialized) ...[
                AspectRatio(
                  aspectRatio: player.value.aspectRatio,
                  child: Stack(
                    alignment: Alignment.center,
                    children: [
                      VideoPlayer(player),
                      IconButton.filled(
                        iconSize: 36,
                        onPressed: () => setState(
                            () => player.value.isPlaying ? player.pause() : player.play()),
                        icon: Icon(player.value.isPlaying ? Icons.pause : Icons.play_arrow),
                      ),
                    ],
                  ),
                ),
                VideoProgressIndicator(player, allowScrubbing: true),
                const SizedBox(height: 12),
                FilledButton.icon(
                  onPressed: _sharing ? null : _share,
                  icon: const Icon(Icons.ios_share),
                  label: Text(_sharing ? 'Baixando…' : 'Salvar ou compartilhar (.mp4)'),
                ),
                const SizedBox(height: 8),
              ] else if (!_rendering)
                const Padding(
                  padding: EdgeInsets.only(bottom: 12),
                  child: Text('Nenhum vídeo gerado ainda.', style: TextStyle(color: SumiColors.ink3)),
                ),
              if (_rendering)
                GeneratingNotice(_stage.isEmpty ? 'Gerando vídeo…' : _stage, progress: _progress)
              else
                OutlinedButton.icon(
                  onPressed: _render,
                  icon: const Icon(Icons.movie_creation_outlined),
                  label: Text(_videoUrl == null ? 'Gerar vídeo' : 'Gerar vídeo de novo'),
                ),
              if (_renderError.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 8),
                  child: Text(_renderError, style: const TextStyle(color: SumiColors.danger)),
                ),
              const SizedBox(height: 16),
              OutlinedButton.icon(
                onPressed: _openYoutube,
                icon: const Icon(Icons.smart_display_outlined),
                label: const Text('Metadados do YouTube'),
              ),
            ],
          ),
        ),
        StepActionBar(
          loading: false,
          enabled: true,
          label: 'Concluir',
          onPressed: () => context.go('/'),
          secondaryLabel: 'Finalizar',
          onSecondary: () => context.go(ProductionStep.finalize.location(widget.projectId)),
        ),
      ],
    );
  }
}

class _YoutubeSheet extends ConsumerStatefulWidget {
  final String projectId;
  const _YoutubeSheet({required this.projectId});

  @override
  ConsumerState<_YoutubeSheet> createState() => _YoutubeSheetState();
}

class _YoutubeSheetState extends ConsumerState<_YoutubeSheet> {
  final _title = TextEditingController();
  final _description = TextEditingController();
  final _tags = TextEditingController();
  String _category = '1';
  String _privacy = 'private';
  YoutubeMetadata _meta = const YoutubeMetadata(categoryId: '1');
  bool _busy = true;

  ProjectsRepository get _repo => ref.read(projectsRepositoryProvider);

  @override
  void initState() {
    super.initState();
    _run(() => _repo.getYoutubeMetadata(widget.projectId));
  }

  @override
  void dispose() {
    _title.dispose();
    _description.dispose();
    _tags.dispose();
    super.dispose();
  }

  void _apply(YoutubeMetadata m) {
    _meta = m;
    _title.text = m.title;
    _description.text = m.description;
    _tags.text = m.tags.join(', ');
    _category = _ytCategories.containsKey(m.categoryId) ? m.categoryId : '1';
    _privacy = _privacyLabels.containsKey(m.privacyStatus) ? m.privacyStatus : 'private';
  }


  Future<void> _run(Future<YoutubeMetadata> Function() action) async {
    setState(() => _busy = true);
    try {
      final m = await action();
      if (mounted) setState(() => _apply(m));
    } catch (_) {
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _save() async {
    await _run(() => _repo.saveYoutubeMetadata(
          widget.projectId,
          YoutubeMetadata(
            title: _title.text.trim(),
            description: _description.text.trim(),
            tags: _tags.text.split(',').map((t) => t.trim()).where((t) => t.isNotEmpty).toList(),
            categoryId: _category,
            privacyStatus: _privacy,
            publishAt: _meta.publishAt,
            thumbnailPanelId: _meta.thumbnailPanelId,
          ),
        ));
    ref.read(notificationServiceProvider).success('Metadados salvos.');
    if (mounted) Navigator.of(context).pop();
  }

  @override
  Widget build(BuildContext context) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.of(context).viewInsets.bottom),
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text('YouTube',
                  style: TextStyle(fontFamily: serifFamily, fontSize: 20, fontWeight: FontWeight.w700)),
              const SizedBox(height: 12),
              OutlinedButton.icon(
                onPressed: _busy ? null : () => _run(() => _repo.generateYoutubeMetadata(widget.projectId)),
                icon: const Icon(Icons.auto_awesome),
                label: const Text('Gerar com IA'),
              ),
              if (_busy) const LinearProgressIndicator(),
              const SizedBox(height: 12),
              TextField(controller: _title, decoration: const InputDecoration(labelText: 'Título')),
              const SizedBox(height: 12),
              TextField(
                controller: _description,
                minLines: 3,
                maxLines: 8,
                decoration: InputDecoration(
                  labelText: 'Descrição',
                  alignLabelWithHint: true,
                  suffixIcon: DictationButton(controller: _description),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _tags,
                decoration: const InputDecoration(labelText: 'Tags', helperText: 'Separe por vírgula.'),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                key: ValueKey('dd-$_category'),
                initialValue: _category,
                decoration: const InputDecoration(labelText: 'Categoria'),
                items: [
                  for (final e in _ytCategories.entries)
                    DropdownMenuItem(value: e.key, child: Text(e.value)),
                ],
                onChanged: (v) => setState(() => _category = v ?? '1'),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                key: ValueKey('dd-$_privacy'),
                initialValue: _privacy,
                decoration: const InputDecoration(labelText: 'Privacidade'),
                items: [
                  for (final e in _privacyLabels.entries) DropdownMenuItem(value: e.key, child: Text(e.value)),
                ],
                onChanged: (v) => setState(() => _privacy = v ?? 'private'),
              ),
              const SizedBox(height: 16),
              FilledButton(
                onPressed: _busy ? null : _save,
                child: const Padding(padding: EdgeInsets.symmetric(vertical: 12), child: Text('Salvar')),
              ),
            ],
          ),
        ),
      );
}
