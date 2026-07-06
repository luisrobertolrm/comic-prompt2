import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map, of, shareReplay } from 'rxjs';

export interface TagSuggestion {
  name: string;
  count: number;
}

interface TagEntry {
  name: string;
  count: number;
  aliases: string[];
}

@Injectable({ providedIn: 'root' })
export class TagCatalogService {
  private http = inject(HttpClient);
  private catalog$: Observable<TagEntry[]> | null = null;

  search(query: string, limit = 10): Observable<TagSuggestion[]> {
    const q = query.trim().toLowerCase().replace(/_/g, ' ');
    if (!q) return of([]);
    return this.load().pipe(
      map(entries => {
        // Buckets por relevância; o CSV já vem ordenado por popularidade.
        const buckets: TagEntry[][] = [[], [], [], []];
        for (const e of entries) {
          if (e.name.startsWith(q)) buckets[0].push(e);
          else if (e.name.includes(q)) buckets[1].push(e);
          else if (e.aliases.some(a => a.startsWith(q))) buckets[2].push(e);
          else if (e.aliases.some(a => a.includes(q))) buckets[3].push(e);
        }
        return buckets
          .flat()
          .slice(0, limit)
          .map(e => ({ name: e.name, count: e.count }));
      }),
    );
  }

  private load(): Observable<TagEntry[]> {
    // URL relativa: resolve contra o <base href>, então funciona sob sub-path.
    this.catalog$ ??= this.http.get('danbooru-tags.csv', { responseType: 'text' }).pipe(
      map(text =>
        text
          .split('\n')
          .filter(Boolean)
          .map(line => {
            const [name, count, aliases] = line.split(',');
            return { name, count: +count, aliases: aliases ? aliases.split('|') : [] };
          }),
      ),
      shareReplay(1),
    );
    return this.catalog$;
  }
}
