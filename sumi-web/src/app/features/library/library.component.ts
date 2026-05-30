import { Component, computed, inject, OnInit, signal } from '@angular/core';
import { Router } from '@angular/router';
import type { CharacterOut } from '../../core/models/home.models';
import { CharacterService } from '../../core/services/character.service';

const PALETTES = ['blush', 'peach', 'mint', 'lilac', 'accent'];
const ROLES = ['Todos', 'Protagonistas', 'Coadjuvantes', 'Mascotes'];

function accentFor(name: string): string {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = ((h * 31) + name.charCodeAt(i)) >>> 0;
  return PALETTES[h % PALETTES.length];
}

@Component({
  selector: 'app-library',
  standalone: true,
  templateUrl: './library.component.html',
  styleUrl: './library.component.scss',
})
export class LibraryComponent implements OnInit {
  private characterService = inject(CharacterService);
  private router = inject(Router);

  readonly roleFilters = ROLES;

  characters = signal<CharacterOut[]>([]);
  loading = signal(true);
  search = signal('');
  roleFilter = signal('Todos');

  filteredChars = computed(() => {
    const q = this.search().toLowerCase();
    const role = this.roleFilter();
    return this.characters().filter(c => {
      const matchSearch = !q || c.name.toLowerCase().includes(q);
      const matchRole = role === 'Todos' || this.matchesRole(c.role, role);
      return matchSearch && matchRole;
    });
  });

  ngOnInit(): void {
    this.characterService.listAll().subscribe({
      next: chars => { this.characters.set(chars); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  private matchesRole(role: string, filter: string): boolean {
    const r = role.toLowerCase();
    if (filter === 'Protagonistas') return r.includes('protagonista') || r.includes('heroi') || r.includes('herói');
    if (filter === 'Coadjuvantes') return r.includes('coadjuvante') || r.includes('interesse') || r.includes('mentor') || r.includes('rival');
    if (filter === 'Mascotes') return r.includes('mascote') || r.includes('animal');
    return true;
  }

  setSearch(e: Event): void {
    this.search.set((e.target as HTMLInputElement).value);
  }

  accentOf(name: string): string { return accentFor(name); }
  initial(name: string): string { return name.charAt(0).toUpperCase(); }

  goNewCharacter(): void { void this.router.navigate(['/projects/new/characters']); }
  goHome(): void { void this.router.navigate(['/home']); }
}
