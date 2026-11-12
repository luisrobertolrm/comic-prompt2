import { Component, inject, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { DictationService } from './core/services/dictation.service';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet],
  templateUrl: './app.html',
  styleUrl: './app.scss'
})
export class App {
  protected readonly title = signal('sumi-web');
  protected dictation = inject(DictationService);

  constructor() {
    this.dictation.listen();
  }
}
