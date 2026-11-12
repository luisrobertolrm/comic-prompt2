import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final GlobalKey<ScaffoldMessengerState> scaffoldMessengerKey =
    GlobalKey<ScaffoldMessengerState>();

final notificationServiceProvider =
    Provider<NotificationService>((ref) => NotificationService());

enum Severity { success, info, warning, error }

/// Ponto único de exibição de mensagens ao usuário (toasts).
class NotificationService {
  void show(Severity severity, String text) {
    final messenger = scaffoldMessengerKey.currentState;
    if (messenger == null || text.isEmpty) return;
    messenger.showSnackBar(SnackBar(
      content: Text(text),
      backgroundColor: _color(severity),
      behavior: SnackBarBehavior.floating,
    ));
  }

  void success(String text) => show(Severity.success, text);
  void info(String text) => show(Severity.info, text);
  void error(String text) => show(Severity.error, text);

  Color? _color(Severity s) => switch (s) {
        Severity.success => Colors.green.shade700,
        Severity.warning => Colors.orange.shade800,
        Severity.error => Colors.red.shade700,
        Severity.info => null,
      };
}
