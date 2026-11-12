import 'package:flutter/material.dart';

import '../../core/theme/app_theme.dart';

/// Barra inferior "Próximo: …" usada por todas as etapas.
class StepActionBar extends StatelessWidget {
  final bool loading;
  final bool enabled;
  final String label;
  final VoidCallback onPressed;
  final String? secondaryLabel;
  final VoidCallback? onSecondary;

  const StepActionBar({
    super.key,
    required this.loading,
    required this.enabled,
    required this.label,
    required this.onPressed,
    this.secondaryLabel,
    this.onSecondary,
  });

  @override
  Widget build(BuildContext context) => SafeArea(
        top: false,
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: const BoxDecoration(
            color: SumiColors.paper,
            border: Border(top: BorderSide(color: SumiColors.rule)),
          ),
          child: Row(
            children: [
              if (secondaryLabel != null && onSecondary != null) ...[
                OutlinedButton(
                  onPressed: loading ? null : onSecondary,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    child: Text(secondaryLabel!),
                  ),
                ),
                const SizedBox(width: 8),
              ],
              Expanded(
                child: FilledButton(
                  onPressed: enabled && !loading ? onPressed : null,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    child: loading
                        ? const SizedBox(
                            width: 18, height: 18, child: CircularProgressIndicator(strokeWidth: 2))
                        : Text('$label →'),
                  ),
                ),
              ),
            ],
          ),
        ),
      );
}
