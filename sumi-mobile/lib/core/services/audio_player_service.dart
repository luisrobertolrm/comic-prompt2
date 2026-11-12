import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:just_audio/just_audio.dart';
import 'package:path_provider/path_provider.dart';

abstract class AudioPlayerService {
  Future<void> playBytes(Uint8List bytes);
  Future<void> playUrl(String url);
  Future<void> stop();
}

class JustAudioPlayerService implements AudioPlayerService {
  final _player = AudioPlayer();

  @override
  Future<void> playBytes(Uint8List bytes) async {
    final dir = await getTemporaryDirectory();
    final file = File('${dir.path}/sumi_voice_test.mp3');
    await file.writeAsBytes(bytes, flush: true);
    await _player.setFilePath(file.path);
    await _player.play();
  }

  @override
  Future<void> playUrl(String url) async {
    await _player.setUrl(url);
    await _player.play();
  }

  @override
  Future<void> stop() => _player.stop();

  void dispose() => _player.dispose();
}

final audioPlayerServiceProvider = Provider<AudioPlayerService>((ref) {
  final service = JustAudioPlayerService();
  ref.onDispose(service.dispose);
  return service;
});
