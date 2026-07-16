import { Component, OnInit, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { environment } from '../../../environments/environment';
import type { PublicProjectOut } from '../../core/models/home.models';
import { AuthService } from '../../core/services/auth.service';
import { PublicService } from '../../core/services/public.service';

const ACCENT_BG: Record<string, string> = {
  accent: '#FBF1DE',
  mint: '#DCEADF',
  peach: '#F6DEC2',
  blush: '#F4D9DA',
  lilac: '#E1D8EC',
};

@Component({
  selector: 'app-gallery',
  standalone: true,
  imports: [RouterLink],
  templateUrl: './gallery.component.html',
  styleUrl: './gallery.component.scss',
})
export class GalleryComponent implements OnInit {
  private publicService = inject(PublicService);
  private router = inject(Router);
  auth = inject(AuthService);

  projects = signal<PublicProjectOut[]>([]);
  loading = signal(true);

  ngOnInit(): void {
    this.publicService.list().subscribe({
      next: ps => { this.projects.set(ps); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  open(p: PublicProjectOut): void {
    void this.router.navigate(['/p', p.id]);
  }

  coverUrl(p: PublicProjectOut): string {
    return p.cover_image_url ? `${environment.apiUrl}${p.cover_image_url}` : '';
  }

  cardBg(p: PublicProjectOut): string {
    return ACCENT_BG[p.cover_accent] ?? '#FBF1DE';
  }

  scrollToGrid(): void {
    document.querySelector('.reader-grid .comic-card')?.scrollIntoView({ behavior: 'smooth' });
  }
}
