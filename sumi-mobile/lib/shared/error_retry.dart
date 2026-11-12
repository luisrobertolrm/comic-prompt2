import 'package:flutter/material.dart';

import '../core/api/api_client.dart';
import '../core/theme/app_theme.dart';

class ErrorRetry extends StatelessWidget {
  final Object error;
  final VoidCallback onRetry;

  const ErrorRetry({super.key, required this.error, required this.onRetry});

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(friendlyError(error),
                textAlign: TextAlign.center, style: const TextStyle(color: SumiColors.ink2)),
            const SizedBox(height: 16),
            OutlinedButton(onPressed: onRetry, child: const Text('Tentar novamente')),
          ],
        ),
      );
}
