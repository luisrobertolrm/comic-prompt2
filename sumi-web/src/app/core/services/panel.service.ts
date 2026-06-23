import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';
import type { PanelOut, PanelPatch } from '../models/panel.models';

@Injectable({ providedIn: 'root' })
export class PanelService {
  private http = inject(HttpClient);
  private base = environment.apiUrl;

  list(projectId: string): Observable<PanelOut[]> {
    return this.http.get<PanelOut[]>(`${this.base}/projects/${projectId}/panels`);
  }

  generate(projectId: string, targetPanels?: number | null): Observable<PanelOut[]> {
    return this.http.post<PanelOut[]>(
      `${this.base}/projects/${projectId}/panels/generate`,
      { target_panels: targetPanels ?? null },
    );
  }

  update(panelId: string, patch: PanelPatch): Observable<PanelOut> {
    return this.http.patch<PanelOut>(`${this.base}/panels/${panelId}`, patch);
  }

  delete(panelId: string): Observable<void> {
    return this.http.delete<void>(`${this.base}/panels/${panelId}`);
  }

  deleteMany(projectId: string, panelIds: string[]): Observable<void> {
    return this.http.post<void>(`${this.base}/projects/${projectId}/panels/delete`, { panel_ids: panelIds });
  }

  insert(projectId: string, afterIndex: number): Observable<PanelOut> {
    return this.http.post<PanelOut>(`${this.base}/projects/${projectId}/panels`, { after_index: afterIndex });
  }

  reorder(projectId: string, panelIds: string[]): Observable<void> {
    return this.http.put<void>(`${this.base}/projects/${projectId}/panels/order`, { panel_ids: panelIds });
  }

  generateContent(panelId: string): Observable<PanelOut> {
    return this.http.post<PanelOut>(`${this.base}/panels/${panelId}/generate`, {});
  }

  generateImage(panelId: string): Observable<PanelOut> {
    return this.http.post<PanelOut>(`${this.base}/panels/${panelId}/image`, {});
  }

  generateBubbles(panelId: string): Observable<PanelOut> {
    return this.http.post<PanelOut>(`${this.base}/panels/${panelId}/bubbles/generate`, {});
  }

  generateAllImages(projectId: string): Observable<PanelOut[]> {
    return this.http.post<PanelOut[]>(
      `${this.base}/projects/${projectId}/panels/generate-images`, {}
    );
  }

  exportZip(projectId: string): Observable<Blob> {
    return this.http.get(
      `${this.base}/projects/${projectId}/export/panels`,
      { responseType: 'blob' }
    );
  }
}
