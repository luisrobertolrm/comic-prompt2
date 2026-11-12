import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../core/api/api_client.dart';

class StyleOption {
  final String id;
  final String label;
  final String note;
  const StyleOption(this.id, this.label, this.note);

  factory StyleOption.fromJson(Map<String, dynamic> j) =>
      StyleOption(j['id'].toString(), j['label'] as String? ?? '', j['note'] as String? ?? '');
}

class StyleCatalog {
  final List<StyleOption> styles;
  final List<StyleOption> colorModes;
  final String defaultStyle;
  final String defaultColorMode;
  const StyleCatalog(this.styles, this.colorModes, this.defaultStyle, this.defaultColorMode);

  factory StyleCatalog.fromJson(Map<String, dynamic> j) => StyleCatalog(
        (j['styles'] as List).map((e) => StyleOption.fromJson((e as Map).cast())).toList(),
        (j['color_modes'] as List).map((e) => StyleOption.fromJson((e as Map).cast())).toList(),
        j['default_style'] as String? ?? '',
        j['default_color_mode'] as String? ?? '',
      );
}

abstract class StylesRepository {
  Future<StyleCatalog> catalog();
}

class ApiStylesRepository implements StylesRepository {
  final Dio _dio;
  ApiStylesRepository(this._dio);

  @override
  Future<StyleCatalog> catalog() async {
    final resp = await _dio.get('/styles');
    return StyleCatalog.fromJson((resp.data as Map).cast<String, dynamic>());
  }
}

final stylesRepositoryProvider =
    Provider<StylesRepository>((ref) => ApiStylesRepository(ref.read(apiClientProvider)));

final styleCatalogProvider =
    FutureProvider<StyleCatalog>((ref) => ref.read(stylesRepositoryProvider).catalog());
