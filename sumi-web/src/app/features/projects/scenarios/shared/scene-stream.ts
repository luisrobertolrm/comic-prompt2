import { DestroyRef } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Observable, switchMap, takeWhile, timer } from 'rxjs';
import { environment } from '../../../../../environments/environment';
import type { SceneJob } from '../../../../core/models/home.models';
import { ScenarioService } from '../../../../core/services/scenario.service';

export interface SceneCandidateUi {
  id: string;
  imageUrl: string;
  notes: string;
}

export interface SceneOpts {
  style: string;
  colorMode: string;
  location?: string;
  timeOfDay?: string;
  weather?: string;
  atmosphere?: string;
  extra?: string;
  prompt?: string;
  raw?: boolean;
}

/** Dispara a geração e faz polling até o job terminar (done/error). */
export function sceneStream(
  service: ScenarioService,
  destroyRef: DestroyRef,
  opts: SceneOpts,
): Observable<SceneJob> {
  return service.generateScene(opts).pipe(
    switchMap(job =>
      timer(0, 3000).pipe(
        switchMap(() => service.pollSceneJob(job.job_id)),
        takeWhile(j => j.status !== 'done' && j.status !== 'error', true),
      )
    ),
    takeUntilDestroyed(destroyRef),
  );
}

export function toSceneCandidates(job: SceneJob): SceneCandidateUi[] {
  return job.scenes.map(c => ({
    id: c.id,
    imageUrl: c.url.startsWith('http') ? c.url : `${environment.apiUrl}${c.url}`,
    notes: c.notes,
  }));
}
