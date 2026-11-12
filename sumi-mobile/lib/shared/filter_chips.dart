import 'package:flutter/material.dart';

import '../core/theme/app_theme.dart';

class FilterChips extends StatelessWidget {
  final List<String> options;
  final String selected;
  final ValueChanged<String> onSelected;

  const FilterChips({
    super.key,
    required this.options,
    required this.selected,
    required this.onSelected,
  });

  @override
  Widget build(BuildContext context) => SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: Row(
          children: [
            for (final option in options)
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ChoiceChip(
                  label: Text(option),
                  selected: option == selected,
                  showCheckmark: false,
                  labelStyle: TextStyle(
                    color: option == selected ? SumiColors.paper : SumiColors.ink2,
                  ),
                  onSelected: (_) => onSelected(option),
                ),
              ),
          ],
        ),
      );
}
