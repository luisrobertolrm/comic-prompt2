import 'dart:io';
import 'dart:typed_data';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';
import 'package:share_plus/share_plus.dart';

abstract class FileShareService {
  Future<void> shareBytes(Uint8List bytes, String fileName, String mimeType);
}

/// A folha de compartilhamento do Android já oferece "Salvar em arquivos".
class SharePlusFileShareService implements FileShareService {
  @override
  Future<void> shareBytes(Uint8List bytes, String fileName, String mimeType) async {
    final dir = await getTemporaryDirectory();
    final file = File('${dir.path}/$fileName');
    await file.writeAsBytes(bytes);
    await SharePlus.instance.share(
      ShareParams(files: [XFile(file.path, mimeType: mimeType)], title: fileName),
    );
  }
}

final fileShareServiceProvider =
    Provider<FileShareService>((ref) => SharePlusFileShareService());
