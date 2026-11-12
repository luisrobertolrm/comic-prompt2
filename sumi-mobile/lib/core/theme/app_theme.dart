import 'package:flutter/material.dart';

/// Cores de `sumi-web/src/styles.scss`.
class SumiColors {
  static const ink = Color(0xFF1E1812);
  static const ink2 = Color(0xFF3D3020);
  static const ink3 = Color(0xFF7D6B52);
  static const ink4 = Color(0xFFB8A898);
  static const paper = Color(0xFFFFFAEC);
  static const paper2 = Color(0xFFF5EDD8);
  static const paper3 = Color(0xFFEDE0C8);
  static const accent = Color(0xFFF0C060);
  static const accentSoft = Color(0xFFFDF0C8);
  static const accentInk = Color(0xFF8B6914);
  static const rule = Color(0xFFD4C4A8);
  static const danger = Color(0xFFB3261E);

  static const _accents = {
    'accent': accent,
    'mint': Color(0xFF7EC8A0),
    'peach': Color(0xFFE8896A),
    'blush': Color(0xFFF4D6D7),
    'lilac': Color(0xFFC8B4E8),
  };

  static const _softs = {
    'accent': accentSoft,
    'mint': Color(0xFFDFF4EB),
    'peach': Color(0xFFFBE8DF),
    'blush': Color(0xFFFDF1F1),
    'lilac': Color(0xFFF0EAF9),
  };

  static Color coverAccent(String key) => _accents[key] ?? accent;
  static Color coverAccentSoft(String key) => _softs[key] ?? accentSoft;

  static const accentKeys = ['accent', 'mint', 'peach', 'blush', 'lilac'];
}

const serifFamily = 'serif';
const monoFamily = 'monospace';

ThemeData buildAppTheme() {
  final scheme = ColorScheme.fromSeed(
    seedColor: SumiColors.accent,
    primary: SumiColors.ink,
    onPrimary: SumiColors.paper,
    secondary: SumiColors.accent,
    onSecondary: SumiColors.ink,
    surface: SumiColors.paper,
    onSurface: SumiColors.ink,
    error: SumiColors.danger,
  );

  return ThemeData(
    useMaterial3: true,
    colorScheme: scheme,
    scaffoldBackgroundColor: SumiColors.paper,
    appBarTheme: const AppBarTheme(
      backgroundColor: SumiColors.paper,
      foregroundColor: SumiColors.ink,
      elevation: 0,
      scrolledUnderElevation: 0,
      shape: Border(bottom: BorderSide(color: SumiColors.rule)),
    ),
    drawerTheme: const DrawerThemeData(backgroundColor: SumiColors.paper2),
    cardTheme: CardThemeData(
      color: Colors.white,
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: const BorderSide(color: SumiColors.rule),
      ),
    ),
    filledButtonTheme: FilledButtonThemeData(
      style: FilledButton.styleFrom(
        backgroundColor: SumiColors.accent,
        foregroundColor: SumiColors.ink,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    ),
    outlinedButtonTheme: OutlinedButtonThemeData(
      style: OutlinedButton.styleFrom(
        foregroundColor: SumiColors.ink,
        side: const BorderSide(color: SumiColors.rule),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
      ),
    ),
    chipTheme: const ChipThemeData(
      backgroundColor: Colors.white,
      selectedColor: SumiColors.ink,
      side: BorderSide(color: SumiColors.rule),
    ),
    inputDecorationTheme: InputDecorationTheme(
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: SumiColors.rule),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(8),
        borderSide: const BorderSide(color: SumiColors.rule),
      ),
    ),
  );
}

class Eyebrow extends StatelessWidget {
  final String text;
  const Eyebrow(this.text, {super.key});

  @override
  Widget build(BuildContext context) => Text(
        text,
        style: const TextStyle(
          fontFamily: monoFamily,
          fontSize: 11,
          letterSpacing: 1.4,
          color: SumiColors.ink3,
        ),
      );
}

class PageTitle extends StatelessWidget {
  final String eyebrow;
  final String title;
  final String? lede;
  const PageTitle({super.key, required this.eyebrow, required this.title, this.lede});

  @override
  Widget build(BuildContext context) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Eyebrow(eyebrow),
          const SizedBox(height: 6),
          Text(title,
              style: const TextStyle(
                  fontFamily: serifFamily, fontSize: 26, fontWeight: FontWeight.w700, height: 1.15)),
          if (lede != null) ...[
            const SizedBox(height: 6),
            Text(lede!, style: const TextStyle(color: SumiColors.ink3)),
          ],
        ],
      );
}
