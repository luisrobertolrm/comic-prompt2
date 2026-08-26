import { Component, ElementRef, OnInit, computed, inject, signal, viewChild } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { environment } from '../../../environments/environment';
import type { PanelOut } from '../../core/models/panel.models';
import { AuthService } from '../../core/services/auth.service';
import { PublicService, type PublicProjectDetailOut } from '../../core/services/public.service';
import { MangaPanelComponent } from '../projects/manga-panel/manga-panel.component';

type ReaderFormat = 'manga-v' | 'grade' | 'dinamico';

const FORMATS: { key: ReaderFormat; label: string; slots: number }[] = [
  { key: 'manga-v', label: 'Mangá vertical', slots: 4 },
  { key: 'grade', label: 'Grade ocidental', slots: 5 },
  { key: 'dinamico', label: 'Dinâmico mangá', slots: 5 },
];

@Component({
  selector: 'app-gallery-reader',
  standalone: true,
  imports: [RouterLink, MangaPanelComponent],
  templateUrl: './gallery-reader.component.html',
  styleUrl: './gallery-reader.component.scss',
})
export class GalleryReaderComponent implements OnInit {
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private publicService = inject(PublicService);
  auth = inject(AuthService);

  formats = FORMATS;
  private id = '';

  project = signal<PublicProjectDetailOut | null>(null);
  loading = signal(true);
  notFound = signal(false);

  format = signal<ReaderFormat>('manga-v');
  page = signal(0);
  watchingVideo = signal(false);
  private player = viewChild<ElementRef<HTMLVideoElement>>('player');

  positivas = signal(0);
  negativas = signal(0);
  minhaReacao = signal<boolean | null>(null);
  loginPrompt = signal(false);
  toast = signal('');
  private toastTimer: ReturnType<typeof setTimeout> | null = null;

  slotsPerPage = computed(() => FORMATS.find(f => f.key === this.format())!.slots);

  pages = computed<PanelOut[][]>(() => {
    const ps = this.project()?.panels ?? [];
    const size = this.slotsPerPage();
    const result: PanelOut[][] = [];
    for (let i = 0; i < ps.length; i += size) result.push(ps.slice(i, i + size));
    return result;
  });

  totalPages = computed(() => Math.max(1, this.pages().length));
  currentPanels = computed(() => this.pages()[this.page()] ?? []);
  dots = computed(() => Array.from({ length: this.totalPages() }, (_, i) => i));

  videoSrc = computed(() => {
    const url = this.project()?.video_url;
    if (!url) return null;
    return url.startsWith('http') ? url : `${environment.apiUrl}${url}`;
  });

  ngOnInit(): void {
    this.id = this.route.snapshot.paramMap.get('id') ?? '';
    this.publicService.get(this.id).subscribe({
      next: p => {
        this.project.set(p);
        this.positivas.set(p.quantidade_positiva);
        this.negativas.set(p.quantidade_negativa);
        this.minhaReacao.set(p.minha_reacao);
        this.loading.set(false);
      },
      error: () => { this.notFound.set(true); this.loading.set(false); },
    });
  }

  setFormat(f: ReaderFormat): void {
    this.pauseVideo();
    this.watchingVideo.set(false);
    this.format.set(f);
    this.page.set(0);
  }

  watchVideo(): void {
    this.watchingVideo.set(true);
  }

  private pauseVideo(): void {
    this.player()?.nativeElement.pause();
  }

  prevPage(): void { this.page.update(p => Math.max(0, p - 1)); }
  nextPage(): void { this.page.update(p => Math.min(this.totalPages() - 1, p + 1)); }

  panelNumber(i: number): string {
    return String(this.page() * this.slotsPerPage() + i + 1).padStart(2, '0');
  }

  react(positivo: boolean): void {
    if (!this.auth.currentUser()) {
      this.loginPrompt.set(true);
      return;
    }
    this.publicService.react(this.id, positivo).subscribe({
      next: r => {
        this.positivas.set(r.quantidade_positiva);
        this.negativas.set(r.quantidade_negativa);
        this.minhaReacao.set(r.minha_reacao);
      },
    });
  }

  goLogin(): void {
    void this.router.navigate(['/auth'], { queryParams: { returnUrl: `/p/${this.id}` } });
  }

  dismissLoginPrompt(): void { this.loginPrompt.set(false); }

  share(): void {
    const done = () => this.showToast('Link copiado!');
    if (navigator.clipboard?.writeText) {
      navigator.clipboard.writeText(window.location.href).then(done).catch(done);
    } else {
      done();
    }
  }

  private showToast(text: string): void {
    this.toast.set(text);
    if (this.toastTimer) clearTimeout(this.toastTimer);
    this.toastTimer = setTimeout(() => this.toast.set(''), 1800);
  }
}
