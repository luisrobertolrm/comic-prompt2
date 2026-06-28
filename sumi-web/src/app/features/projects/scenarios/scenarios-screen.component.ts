import { Component, DestroyRef, computed, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import type { AttrOption, ScenarioCreate, ScenarioOut, ScenarioUpdate } from '../../../core/models/home.models';
import { ProjectDraftService } from '../../../core/services/project-draft.service';
import { ProjectService } from '../../../core/services/project.service';
import { ScenarioService } from '../../../core/services/scenario.service';
import { StyleService, type StyleOption } from '../../../core/services/style.service';
import { SceneCandidateUi, sceneStream, toSceneCandidates } from './shared/scene-stream';

type Tab = 'library' | 'ai';
type AiMode = 'prompt' | 'attrs';

@Component({
  selector: 'app-scenarios-screen',
  standalone: true,
  imports: [],
  templateUrl: './scenarios-screen.component.html',
  styleUrl: './scenarios-screen.component.scss',
})
export class ScenariosScreenComponent implements OnInit {
  private router = inject(Router);
  private draftService = inject(ProjectDraftService);
  private scenarioService = inject(ScenarioService);
  private projectService = inject(ProjectService);
  private styleService = inject(StyleService);
  private destroyRef = inject(DestroyRef);

  tab = signal<Tab>('library');
  scenarios = signal<ScenarioOut[]>([]);
  projectStyle = signal('anime-90s');
  projectColorMode = signal('tons-cinza');
  selectedIds = signal<Set<string>>(new Set());
  loading = signal(true);
  saving = signal(false);

  locations = signal<AttrOption[]>([]);
  timesOfDay = signal<AttrOption[]>([]);
  weathers = signal<AttrOption[]>([]);
  atmospheres = signal<AttrOption[]>([]);
  private styleCatalog = signal<StyleOption[]>([]);
  styleLabel = computed(() =>
    this.styleCatalog().find(s => s.id === this.projectStyle())?.label ?? this.projectStyle()
  );

  selectedCount = computed(() => this.selectedIds().size);
  deletableUnused = computed(() =>
    this.scenarios().filter(s => s.project_count === 0 && !this.selectedIds().has(s.id))
  );
  confirmDeleteUnused = signal(false);
  deletingUnused = signal(false);

  // ── Aba IA ──
  aiMode = signal<AiMode>('attrs');
  aiName = signal('');
  aiKind = signal('');
  aiLocation = signal('');
  aiTime = signal('');
  aiWeather = signal('');
  aiAtmosphere = signal('');
  aiExtra = signal('');
  aiPrompt = signal('Um pátio de castelo medieval ao entardecer, muralhas de pedra cobertas de hera, tochas acesas, céu alaranjado. Sem pessoas.');
  aiGenerating = signal(false);
  aiError = signal('');
  aiCandidates = signal<SceneCandidateUi[]>([]);
  aiPicked = signal<string | null>(null);
  aiSaving = signal(false);

  // ── Modal de edição ──
  editing = signal<ScenarioOut | null>(null);
  eName = signal('');
  eKind = signal('');
  eSummary = signal('');
  eDetails = signal('');
  eLocation = signal('');
  eTime = signal('');
  eWeather = signal('');
  eAtmosphere = signal('');
  eImageUrl = signal<string | null>(null);
  eGenerating = signal(false);
  eError = signal('');
  eCandidates = signal<SceneCandidateUi[]>([]);
  ePicked = signal<string | null>(null);
  eSaving = signal(false);
  eRegenWarn = signal(false);

  ngOnInit(): void {
    this.styleService.catalog().subscribe({ next: c => this.styleCatalog.set(c.styles) });

    this.scenarioService.options().subscribe({
      next: groups => {
        this.locations.set(groups.find(g => g.id === 'location')?.options ?? []);
        this.timesOfDay.set(groups.find(g => g.id === 'time_of_day')?.options ?? []);
        this.weathers.set(groups.find(g => g.id === 'weather')?.options ?? []);
        this.atmospheres.set(groups.find(g => g.id === 'atmosphere')?.options ?? []);
      },
    });

    this.scenarioService.listAll().subscribe({
      next: list => { this.scenarios.set(list); this.loading.set(false); },
      error: () => this.loading.set(false),
    });

    const projectId = this.draftService.projectId();
    if (projectId) {
      this.projectService.get(projectId).subscribe({
        next: p => {
          this.selectedIds.set(new Set(p.scenarios.map(s => s.id)));
          this.projectStyle.set(p.style);
          this.projectColorMode.set(p.color_mode ?? 'tons-cinza');
        },
      });
    }
  }

  toggleScenario(id: string): void {
    const s = new Set(this.selectedIds());
    if (s.has(id)) s.delete(id); else s.add(id);
    this.selectedIds.set(s);
  }

  isSelected(id: string): boolean {
    return this.selectedIds().has(id);
  }

  initial(name: string): string {
    return name.charAt(0).toUpperCase();
  }

  setField(sig: ReturnType<typeof signal<string>>, e: Event): void {
    sig.set((e.target as HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement).value);
  }

  deleteUnused(): void {
    const ids = this.deletableUnused().map(s => s.id);
    if (ids.length === 0 || this.deletingUnused()) return;
    this.deletingUnused.set(true);
    this.scenarioService.deleteUnused(ids).subscribe({
      next: () => {
        const removed = new Set(ids);
        this.scenarios.update(list => list.filter(s => !removed.has(s.id)));
        this.deletingUnused.set(false);
        this.confirmDeleteUnused.set(false);
      },
      error: () => this.deletingUnused.set(false),
    });
  }

  // ── Aba IA ──

  aiGenerate(): void {
    this.aiGenerating.set(true);
    this.aiError.set('');
    this.aiCandidates.set([]);
    this.aiPicked.set(null);

    const stream = this.aiMode() === 'attrs'
      ? sceneStream(this.scenarioService, this.destroyRef, {
          style: this.projectStyle(),
          colorMode: this.projectColorMode(),
          location: this.aiLocation() || undefined,
          timeOfDay: this.aiTime() || undefined,
          weather: this.aiWeather() || undefined,
          atmosphere: this.aiAtmosphere() || undefined,
          extra: this.aiExtra() || undefined,
        })
      : sceneStream(this.scenarioService, this.destroyRef, {
          style: this.projectStyle(),
          colorMode: this.projectColorMode(),
          prompt: this.aiPrompt(),
          raw: true,
        });

    stream.subscribe({
      next: job => {
        if (job.status === 'done') {
          this.aiCandidates.set(toSceneCandidates(job));
          this.aiGenerating.set(false);
        } else if (job.status === 'error') {
          this.aiError.set(job.detail || 'Erro ao gerar cenários.');
          this.aiGenerating.set(false);
        }
      },
      error: err => {
        this.aiGenerating.set(false);
        this.aiError.set(err?.error?.detail ?? err?.message ?? 'Erro ao gerar cenários.');
      },
    });
  }

  pickAiCandidate(id: string): void {
    this.aiPicked.set(this.aiPicked() === id ? null : id);
  }

  aiConfirm(): void {
    if (!this.aiPicked() || !this.aiName().trim() || this.aiSaving()) return;
    const picked = this.aiCandidates().find(c => c.id === this.aiPicked());
    this.aiSaving.set(true);
    const req: ScenarioCreate = {
      name: this.aiName(),
      kind: this.aiKind() || 'Cenário',
      summary: this.aiMode() === 'prompt'
        ? this.aiPrompt()
        : [this.aiExtra()].filter(v => v.trim()).join(', ') || undefined,
      location_type: this.aiLocation() || undefined,
      time_of_day: this.aiTime() || undefined,
      weather: this.aiWeather() || undefined,
      atmosphere: this.aiAtmosphere() || undefined,
      style: this.projectStyle(),
      image_url: picked?.imageUrl,
    };
    this.scenarioService.create(req).subscribe({
      next: scenario => {
        this.scenarios.update(list => [...list, scenario]);
        this.toggleScenario(scenario.id);
        this.aiCandidates.set([]); this.aiPicked.set(null); this.aiName.set(''); this.aiKind.set('');
        this.aiSaving.set(false);
        this.tab.set('library');
      },
      error: () => this.aiSaving.set(false),
    });
  }

  // ── Modal de edição ──

  openEdit(s: ScenarioOut): void {
    this.editing.set(s);
    this.eName.set(s.name);
    this.eKind.set(s.kind);
    this.eSummary.set(s.summary ?? '');
    this.eDetails.set(s.details ?? '');
    this.eLocation.set(s.location_type ?? '');
    this.eTime.set(s.time_of_day ?? '');
    this.eWeather.set(s.weather ?? '');
    this.eAtmosphere.set(s.atmosphere ?? '');
    this.eImageUrl.set(s.image_url);
    this.eGenerating.set(false);
    this.eError.set('');
    this.eCandidates.set([]);
    this.ePicked.set(null);
    this.eRegenWarn.set(false);
  }

  closeEdit(): void {
    this.editing.set(null);
  }

  private buildEditReq(): ScenarioUpdate {
    return {
      name: this.eName(),
      kind: this.eKind() || 'Cenário',
      summary: this.eSummary() || null,
      details: this.eDetails() || null,
      location_type: this.eLocation() || null,
      time_of_day: this.eTime() || null,
      weather: this.eWeather() || null,
      atmosphere: this.eAtmosphere() || null,
    };
  }

  regenScene(force = false): void {
    if (this.eGenerating()) return;
    const ed = this.editing();
    if (!ed) return;
    if (!this.eName().trim()) {
      this.eError.set('Informe o nome antes de regerar.');
      return;
    }
    if (!force && ed.project_count > 0) {
      this.eRegenWarn.set(true);
      return;
    }
    this.eRegenWarn.set(false);
    this.eGenerating.set(true);
    this.eError.set('');

    this.scenarioService.update(ed.id, this.buildEditReq()).subscribe({
      next: scenario => {
        this.scenarios.update(list => list.map(s => (s.id === scenario.id ? scenario : s)));
        this.runSceneRegen();
      },
      error: err => {
        this.eGenerating.set(false);
        this.eError.set(err?.error?.detail ?? err?.message ?? 'Falha ao salvar antes de regerar.');
      },
    });
  }

  private runSceneRegen(): void {
    this.eCandidates.set([]);
    this.ePicked.set(null);
    sceneStream(this.scenarioService, this.destroyRef, {
      style: this.projectStyle(),
      colorMode: this.projectColorMode(),
      location: this.eLocation() || undefined,
      timeOfDay: this.eTime() || undefined,
      weather: this.eWeather() || undefined,
      atmosphere: this.eAtmosphere() || undefined,
      extra: this.eDetails() || this.eSummary() || undefined,
    }).subscribe({
      next: job => {
        if (job.status === 'done') {
          this.eCandidates.set(toSceneCandidates(job));
          this.eGenerating.set(false);
        } else if (job.status === 'error') {
          this.eError.set(job.detail || 'Erro ao gerar cenários.');
          this.eGenerating.set(false);
        }
      },
      error: err => {
        this.eGenerating.set(false);
        this.eError.set(err?.error?.detail ?? err?.message ?? 'Erro ao gerar cenários.');
      },
    });
  }

  pickEditCandidate(id: string): void {
    this.ePicked.set(this.ePicked() === id ? null : id);
  }

  saveEdit(): void {
    const current = this.editing();
    if (!current || !this.eName().trim() || this.eSaving()) return;
    this.eSaving.set(true);

    const picked = this.eCandidates().find(c => c.id === this.ePicked());
    const req: ScenarioUpdate = this.buildEditReq();
    if (picked) req.image_url = picked.imageUrl;

    this.scenarioService.update(current.id, req).subscribe({
      next: scenario => {
        this.scenarios.update(list => list.map(s => (s.id === scenario.id ? scenario : s)));
        this.eSaving.set(false);
        this.closeEdit();
      },
      error: () => this.eSaving.set(false),
    });
  }

  // ── Navegação ──

  advance(): void {
    if (this.saving()) return;
    const projectId = this.draftService.projectId();
    if (!projectId) {
      void this.router.navigate(['/projects/new']);
      return;
    }
    this.saving.set(true);
    this.projectService.setScenarios(projectId, [...this.selectedIds()]).subscribe({
      next: () => {
        this.draftService.projectId.set(null);
        void this.router.navigate(['/projects', projectId, 'script']);
      },
      error: () => this.saving.set(false),
    });
  }

  skip(): void {
    const projectId = this.draftService.projectId();
    if (!projectId) {
      void this.router.navigate(['/projects/new']);
      return;
    }
    this.draftService.projectId.set(null);
    void this.router.navigate(['/projects', projectId, 'script']);
  }

  back(): void {
    void this.router.navigate(['/projects/new/characters']);
  }
}
