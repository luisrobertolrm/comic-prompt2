import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/auth/auth_provider.dart';
import '../../core/theme/app_theme.dart';
import '../auth/login_screen.dart';

class _MenuItem {
  final String label;
  final String path;
  final IconData icon;
  const _MenuItem(this.label, this.path, this.icon);
}

const _menu = [
  _MenuItem('Início', '/', Icons.home_outlined),
  _MenuItem('Projetos', '/projects', Icons.auto_stories_outlined),
  _MenuItem('Biblioteca', '/library', Icons.people_outline),
  _MenuItem('Séries', '/series', Icons.view_quilt_outlined),
  _MenuItem('Teste de Voz', '/voice-test', Icons.mic_none),
];

class ShellScaffold extends ConsumerWidget {
  final String location;
  final Widget child;

  const ShellScaffold({super.key, required this.location, required this.child});

  int get _selectedIndex {
    for (var i = _menu.length - 1; i > 0; i--) {
      if (location.startsWith(_menu[i].path)) return i;
    }
    return 0;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final user = ref.watch(authProvider).user;
    final selected = _selectedIndex;

    return Scaffold(
      appBar: AppBar(title: Text(_menu[selected].label)),
      drawer: NavigationDrawer(
        selectedIndex: selected,
        onDestinationSelected: (i) {
          Navigator.of(context).pop();
          context.go(_menu[i].path);
        },
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 12),
            child: Row(
              children: [
                const BrandMark(),
                const SizedBox(width: 10),
                const Text('Sumi',
                    style: TextStyle(
                        fontFamily: serifFamily, fontSize: 20, fontWeight: FontWeight.w700)),
              ],
            ),
          ),
          if (user != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 12),
              child: Row(
                children: [
                  CircleAvatar(
                    backgroundColor: SumiColors.accent,
                    foregroundColor: SumiColors.ink,
                    child: Text(user.initial),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(user.name, style: const TextStyle(fontWeight: FontWeight.w600)),
                        Text(user.email ?? user.plan,
                            style: const TextStyle(color: SumiColors.ink3, fontSize: 12)),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          const Divider(indent: 20, endIndent: 20),
          const Padding(
            padding: EdgeInsets.fromLTRB(28, 8, 16, 8),
            child: Eyebrow('ATALHOS'),
          ),
          for (final item in _menu)
            NavigationDrawerDestination(icon: Icon(item.icon), label: Text(item.label)),
          const Divider(indent: 20, endIndent: 20),
          ListTile(
            contentPadding: const EdgeInsets.symmetric(horizontal: 28),
            leading: const Icon(Icons.logout, color: SumiColors.danger),
            title: const Text('Sair', style: TextStyle(color: SumiColors.danger)),
            onTap: () {
              Navigator.of(context).pop();
              ref.read(authProvider.notifier).logout();
            },
          ),
        ],
      ),
      body: child,
    );
  }
}
