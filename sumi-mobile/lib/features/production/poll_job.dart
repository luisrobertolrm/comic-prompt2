import 'dart:async';

import 'package:flutter/widgets.dart';

import 'jobs.dart';

/// Consulta um job do servidor a cada 2 s até `done`/`error`.
/// Ao voltar ao app (`resumed`) consulta na hora; `cancel()` para ao descartar a tela.
class JobPoller with WidgetsBindingObserver {
  final Future<Job> Function() fetch;
  final void Function(Job job) onUpdate;
  final void Function(Object error)? onError;

  Timer? _timer;
  bool _running = false;
  bool _cancelled = false;

  JobPoller({required this.fetch, required this.onUpdate, this.onError}) {
    WidgetsBinding.instance.addObserver(this);
    _schedule(Duration.zero);
  }

  void _schedule(Duration delay) {
    _timer?.cancel();
    if (_cancelled) return;
    _timer = Timer(delay, _tick);
  }

  Future<void> _tick() async {
    if (_running || _cancelled) return;
    _running = true;
    try {
      final job = await fetch();
      if (_cancelled) return;
      onUpdate(job);
      if (job.isFinished) {
        cancel();
        return;
      }
    } catch (e) {
      onError?.call(e);
    } finally {
      _running = false;
    }
    _schedule(const Duration(seconds: 2));
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) _schedule(Duration.zero);
  }

  void cancel() {
    _cancelled = true;
    _timer?.cancel();
    WidgetsBinding.instance.removeObserver(this);
  }
}

/// Recarrega dados ao voltar ao app — usado nas gerações síncronas (R7).
class ResumeListener with WidgetsBindingObserver {
  final VoidCallback onResume;

  ResumeListener(this.onResume) {
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) onResume();
  }

  void dispose() => WidgetsBinding.instance.removeObserver(this);
}
