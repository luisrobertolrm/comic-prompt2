import { DestroyRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Observable, switchMap, takeWhile, timer } from 'rxjs';
import { environment } from '../../../../../environments/environment';
import type { PortraitJob } from '../../../../core/models/home.models';
import { CharacterService } from '../../../../core/services/character.service';

export interface AiCandidate {
  id: string;
  imageUrl: string;
  notes: string;
}

export interface PortraitOpts {
  style: string;
  colorMode: string;
  gender?: string;
  ageRange?: string;
  ethnicity?: string;
  hair?: string;
  extra?: string;
  prompt?: string;
  raw?: boolean;
}

/** Dispara a geração e faz polling até o job terminar (done/error). */
export function portraitStream(
  service: CharacterService,
  destroyRef: DestroyRef,
  opts: PortraitOpts,
): Observable<PortraitJob> {
  return service.generatePortrait(opts).pipe(
    switchMap(job =>
      timer(0, 3000).pipe(
        switchMap(() => service.pollPortraitJob(job.job_id)),
        takeWhile(j => j.status !== 'done' && j.status !== 'error', true),
      )
    ),
    takeUntilDestroyed(destroyRef),
  );
}

export function toCandidates(job: PortraitJob): AiCandidate[] {
  return job.portraits.map(c => ({
    id: c.id,
    imageUrl: c.url.startsWith('http') ? c.url : `${environment.apiUrl}${c.url}`,
    notes: c.notes,
  }));
}
