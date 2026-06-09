# Fix: targetPanels não propagado até o backend

## Erro

```
TS2554: Expected 1 arguments, but got 2.
src/app/features/projects/script/script.component.ts:57
  this.panelService.generate(this.projectId(), this.targetPanels())
```

---

## Causa

O componente passou a enviar `targetPanels` (quantidade desejada de quadros) para
`PanelService.generate`, mas nenhuma das camadas abaixo aceita esse parâmetro.

---

## Classes/arquivos envolvidos

### Angular

| Arquivo | Classe / símbolo | Problema |
|---------|-----------------|---------|
| `sumi-web/src/app/features/projects/script/script.component.ts` | `ScriptComponent.runGenerate()` L57 | Chama `generate(projectId, targetPanels())` — 2 args |
| `sumi-web/src/app/core/services/panel.service.ts` | `PanelService.generate(projectId: string)` L16 | Só aceita 1 arg; não passa nada no body do POST |

### Python

| Arquivo | Função | Problema |
|---------|--------|---------|
| `sumi-api/src/prompt_clinica/routers/projects.py` | `generate_panels()` L89 | Endpoint sem body — não recebe `count` |
| `sumi-api/src/prompt_clinica/services/panel_service.py` | `generate(project_id, user, db)` L208 | Sem parâmetro `count`; não passa quantidade para `generate_roteiro` |

---

## O que precisa mudar para implementar `count`

1. **`panel_service.py` (Python)** — adicionar `count: int | None = None` e
   repassar para `generate_roteiro`.

2. **`routers/projects.py` (Python)** — criar um Pydantic body
   `class GeneratePanelsBody(BaseModel): count: int | None = None` e injetar
   no endpoint.

3. **`panel.service.ts` (Angular)** — mudar assinatura para
   `generate(projectId: string, count?: number | null)` e incluir `{ count }`
   no body do POST.

4. **`script.component.ts` (Angular)** — a chamada `generate(this.projectId(), this.targetPanels())` já está correta; bastará compilar depois das mudanças acima.

---

## Solução alternativa (rápida)

Se `targetPanels` ainda **não** precisa ser enviado ao backend, basta remover
o segundo argumento na linha 57:

```ts
// antes
this.panelService.generate(this.projectId(), this.targetPanels()).subscribe({

// depois
this.panelService.generate(this.projectId()).subscribe({
```



Erro no npm start:

╰─ ❯ npm start

> sumi-web@0.0.0 start
> ng serve

Application bundle generation failed. [6.372 seconds] - 2026-06-09T01:43:14.632Z

▲ [WARNING] NG8102: NG8102: The left side of this nullish coalescing operation does not include 'null' or 'undefined' in its type, therefore the '??' operator can be safely removed. Find more at https://v21.angular.dev/extended-diagnostics/NG8102 [plugin angular-compiler]

    src/app/features/projects/review/review.component.html:144:51:
      144 │                 <select class="select-sm" [value]="b.tail ?? 'none'"
          ╵                                                    ~~~~~~~~~~~~~~~~

  Warning occurs in the template of component ReviewComponent.

    src/app/features/projects/review/review.component.ts:18:15:
      18 │   templateUrl: './review.component.html',
         ╵                ~~~~~~~~~~~~~~~~~~~~~~~~~


▲ [WARNING] NG8107: NG8107: The left side of this optional chain operation does not include 'null' or 'undefined' in its type, therefore the '?.' operator can be replaced with the '.' operator. Find more at https://v21.angular.dev/extended-diagnostics/NG8107 [plugin angular-compiler]

    src/app/features/projects/video/video.component.html:122:67:
      122 │ ...ave-bar--active]="playing() && beat()?.text && !curVoice().muted"
          ╵                                           ~~~~

  Warning occurs in the template of component VideoComponent.

    src/app/features/projects/video/video.component.ts:97:15:
      97 │   templateUrl: './video.component.html',
         ╵                ~~~~~~~~~~~~~~~~~~~~~~~~


▲ [WARNING] NG8107: NG8107: The left side of this optional chain operation does not include 'null' or 'undefined' in its type, therefore the '?.' operator can be replaced with the '.' operator. Find more at https://v21.angular.dev/extended-diagnostics/NG8107 [plugin angular-compiler]

    src/app/features/projects/video/video.component.html:129:45:
      129 │ ...an class="muted">{{ beat()?.speaker }} está mudo nesta prévi...
          ╵                                ~~~~~~~

  Warning occurs in the template of component VideoComponent.

    src/app/features/projects/video/video.component.ts:97:15:
      97 │   templateUrl: './video.component.html',
         ╵                ~~~~~~~~~~~~~~~~~~~~~~~~


▲ [WARNING] NG8107: NG8107: The left side of this optional chain operation does not include 'null' or 'undefined' in its type, therefore the '?.' operator can be replaced with the '.' operator. Find more at https://v21.angular.dev/extended-diagnostics/NG8107 [plugin angular-compiler]

    src/app/features/projects/video/video.component.html:130:45:
      130 │             } @else if (playing() && beat()?.text) {
          ╵                                              ~~~~

  Warning occurs in the template of component VideoComponent.

    src/app/features/projects/video/video.component.ts:97:15:
      97 │   templateUrl: './video.component.html',
         ╵                ~~~~~~~~~~~~~~~~~~~~~~~~


▲ [WARNING] NG8107: NG8107: The left side of this optional chain operation does not include 'null' or 'undefined' in its type, therefore the '?.' operator can be replaced with the '.' operator. Find more at https://v21.angular.dev/extended-diagnostics/NG8107 [plugin angular-compiler]

    src/app/features/projects/video/video.component.html:200:70:
      200 │ ...class.voice-row--active]="beat()?.speaker === name && playing()">
          ╵                                      ~~~~~~~

  Warning occurs in the template of component VideoComponent.

    src/app/features/projects/video/video.component.ts:97:15:
      97 │   templateUrl: './video.component.html',
         ╵                ~~~~~~~~~~~~~~~~~~~~~~~~


▲ [WARNING] NG8107: NG8107: The left side of this optional chain operation does not include 'null' or 'undefined' in its type, therefore the '?.' operator can be replaced with the '.' operator. Find more at https://v21.angular.dev/extended-diagnostics/NG8107 [plugin angular-compiler]

    src/app/features/projects/video/video.component.html:228:60:
      228 │ ...        CENA {{ padNum(sceneIdx() + 1) }} · {{ scene()?.label }}
          ╵                                                           ~~~~~

  Warning occurs in the template of component VideoComponent.

    src/app/features/projects/video/video.component.ts:97:15:
      97 │   templateUrl: './video.component.html',
         ╵                ~~~~~~~~~~~~~~~~~~~~~~~~


X [ERROR] TS2554: Expected 1 arguments, but got 2. [plugin angular-compiler]

    src/app/features/projects/script/script.component.ts:57:49:
      57 │ ...ervice.generate(this.projectId(), this.targetPanels()).subscribe({
         ╵                                      ~~~~~~~~~~~~~~~~~~~


Watch mode enabled. Watching for file changes...