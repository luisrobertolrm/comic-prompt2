import { Component, OnInit, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import type { PendingUserOut } from '../../core/models/auth.models';
import { AdminService } from '../../core/services/admin.service';

@Component({
  selector: 'app-admin',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './admin.component.html',
  styleUrl: './admin.component.scss',
})
export class AdminComponent implements OnInit {
  private adminService = inject(AdminService);

  pending = signal<PendingUserOut[]>([]);
  loading = signal(true);
  busyId = signal('');

  ngOnInit(): void {
    this.adminService.listPending().subscribe({
      next: users => { this.pending.set(users); this.loading.set(false); },
      error: () => this.loading.set(false),
    });
  }

  approve(u: PendingUserOut): void {
    this.busyId.set(u.id);
    this.adminService.approve(u.id).subscribe({
      next: () => { this.remove(u.id); this.busyId.set(''); },
      error: () => this.busyId.set(''),
    });
  }

  reject(u: PendingUserOut): void {
    this.busyId.set(u.id);
    this.adminService.reject(u.id).subscribe({
      next: () => { this.remove(u.id); this.busyId.set(''); },
      error: () => this.busyId.set(''),
    });
  }

  private remove(id: string): void {
    this.pending.update(list => list.filter(u => u.id !== id));
  }
}
