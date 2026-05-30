import { Component, inject, signal } from '@angular/core';
import {
  AbstractControl,
  FormControl,
  FormGroup,
  ReactiveFormsModule,
  ValidationErrors,
  Validators,
} from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';

function passwordsMatch(group: AbstractControl): ValidationErrors | null {
  const pw = group.get('password')?.value as string;
  const confirm = group.get('confirm')?.value as string;
  return pw && confirm && pw !== confirm ? { passwordsMismatch: true } : null;
}

type Mode = 'login' | 'register';

@Component({
  selector: 'app-auth-screen',
  standalone: true,
  imports: [ReactiveFormsModule],
  templateUrl: './auth-screen.component.html',
  styleUrl: './auth-screen.component.scss',
})
export class AuthScreenComponent {
  private authService = inject(AuthService);
  private router = inject(Router);

  mode = signal<Mode>('login');
  loading = signal(false);
  serverError = signal('');
  resetSent = signal(false);

  loginForm = new FormGroup({
    email: new FormControl('', [Validators.required, Validators.email]),
    password: new FormControl('', [Validators.required, Validators.minLength(6)]),
    remember: new FormControl(true),
  });

  registerForm = new FormGroup(
    {
      name: new FormControl('', [Validators.required]),
      email: new FormControl('', [Validators.required, Validators.email]),
      password: new FormControl('', [Validators.required, Validators.minLength(6)]),
      confirm: new FormControl('', [Validators.required]),
      terms: new FormControl(false, [Validators.requiredTrue]),
    },
    { validators: passwordsMatch },
  );

  setMode(m: Mode): void {
    this.mode.set(m);
    this.serverError.set('');
    this.loginForm.reset({ remember: true });
    this.registerForm.reset();
  }

  submitLogin(): void {
    if (this.loginForm.invalid) {
      this.loginForm.markAllAsTouched();
      return;
    }
    const { email, password, remember } = this.loginForm.value;
    this.loading.set(true);
    this.serverError.set('');

    this.authService
      .login({ email: email!, password: password!, remember: remember ?? false })
      .subscribe({
        next: () => {
          void this.router.navigate(['/home']);
          this.loading.set(false);
        },
        error: (err: Error) => {
          this.serverError.set(err.message);
          this.loading.set(false);
        },
      });
  }

  submitRegister(): void {
    if (this.registerForm.invalid) {
      this.registerForm.markAllAsTouched();
      return;
    }
    const { name, email, password, confirm, terms } = this.registerForm.value;
    this.loading.set(true);
    this.serverError.set('');

    this.authService
      .register({
        name: name!,
        email: email!,
        password: password!,
        confirm: confirm!,
        terms_accepted: terms!,
      })
      .subscribe({
        next: () => {
          void this.router.navigate(['/home']);
          this.loading.set(false);
        },
        error: (err: Error) => {
          this.serverError.set(err.message);
          this.loading.set(false);
        },
      });
  }

  loginAsGuest(): void {
    this.loading.set(true);
    this.authService.loginAsGuest().subscribe({
      next: () => { void this.router.navigate(['/home']); },
      error: (err: Error) => {
        this.serverError.set(err.message);
        this.loading.set(false);
      },
    });
  }

  requestReset(): void {
    const email = this.loginForm.get('email')?.value;
    if (!email) {
      this.serverError.set('Preencha o e-mail antes de solicitar a recuperação.');
      return;
    }
    this.authService.requestPasswordReset(email).subscribe({
      next: () => this.resetSent.set(true),
      error: () => this.resetSent.set(true), // nunca revela existência
    });
  }

  // Helpers para erros nos templates
  loginError(field: string): string {
    const ctrl = this.loginForm.get(field);
    if (!ctrl || !ctrl.touched || ctrl.valid) return '';
    if (ctrl.hasError('required')) return 'Campo obrigatório.';
    if (ctrl.hasError('email')) return 'E-mail inválido.';
    if (ctrl.hasError('minlength')) return 'Mínimo de 6 caracteres.';
    return '';
  }

  registerError(field: string): string {
    const ctrl = this.registerForm.get(field);
    if (!ctrl || !ctrl.touched || ctrl.valid) return '';
    if (ctrl.hasError('required')) return field === 'name' ? 'Como devemos te chamar?' : 'Campo obrigatório.';
    if (ctrl.hasError('email')) return 'E-mail inválido.';
    if (ctrl.hasError('minlength')) return 'Mínimo de 6 caracteres.';
    if (field === 'terms') return 'Aceite os termos para continuar.';
    return '';
  }

  get confirmError(): string {
    if (!this.registerForm.get('confirm')?.touched) return '';
    if (this.registerForm.hasError('passwordsMismatch')) return 'As senhas não conferem.';
    return '';
  }
}
