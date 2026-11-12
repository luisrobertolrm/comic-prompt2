# Sumi — app Android

App Flutter com os menus do Sumi web (Início, Projetos, Biblioteca, Séries, Teste de Voz) e o
fluxo completo de produção (Ideia → Personagens → Cenários → Roteiro → Revisão → Editor →
Finalizar → Vídeo). Consome a mesma API do `sumi-api/`.

Especificação e plano: `specs/001-mobile-app-menus/`.

## Pré-requisitos

- Flutter 3.41+ com Android SDK (`flutter doctor` sem erros para Android)
- `sumi-api` rodando e acessível pelo aparelho
- ~5 GB livres em disco para o primeiro build (cache do Gradle)

## Rodar

```powershell
cd sumi-mobile
flutter pub get
flutter analyze
flutter run --dart-define=API_BASE_URL=http://<IP-DA-API>:8000
```

`API_BASE_URL`: no emulador use `http://10.0.2.2:8000`; em aparelho físico, o IP da máquina na
rede local (não `localhost`). Sem o define, o padrão é `http://10.0.2.2:8000`.

APK de teste:

```powershell
flutter build apk --debug --dart-define=API_BASE_URL=http://<IP-DA-API>:8000
```

## Estrutura

```text
lib/
├── core/       api (Dio + interceptor), auth (login + renovação), router, services, storage, theme
├── features/   uma pasta por menu; production/ tem as 8 etapas
└── shared/     widgets reutilizados (capa, filtros, estado vazio, erro)
```

Todo acesso à API passa por um repositório abstrato (`abstract class XRepository`) com a
implementação `ApiXRepository`; as telas só conhecem a abstração.

## Validação

Cenários manuais em `specs/001-mobile-app-menus/quickstart.md`.
