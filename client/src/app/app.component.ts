import { Component, OnInit, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule],
  template: `
    <div class="admin-shell">
      <header class="topbar">
        <div class="brand">
          <span class="dot"></span>
          <h1>AutoCameraAI Admin</h1>
          <span class="badge">{{ version() }}</span>
        </div>
        <div class="actions">
          <button class="btn-update" (click)="checkForUpdate()" [disabled]="checking()">
            {{ checking() ? 'Đang kiểm tra...' : '🔄 Kiểm tra cập nhật' }}
          </button>
        </div>
      </header>

      <main class="content">
        <div class="card">
          <h2>Hệ thống Quản trị AutoCameraAI-Admin</h2>
          <p>Môi trường Client (Angular) + Backend (Python FastAPI / Desktop EXE) đã sẵn sàng.</p>

          @if (statusMessage()) {
            <div class="alert">{{ statusMessage() }}</div>
          }

          @if (updateInfo()) {
            <div class="update-box">
              <p>🚀 Đã có phiên bản mới: <strong>v{{ updateInfo()?.version }}</strong></p>
              <button class="btn-install" (click)="installUpdate()" [disabled]="updating()">
                {{ updating() ? 'Đang tải & nâng cấp (' + progress() + '%)...' : '⚡ Cập nhật ngay' }}
              </button>
            </div>
          }
        </div>
      </main>
    </div>
  `,
  styles: [`
    .admin-shell { min-height: 100vh; display: flex; flex-direction: column; }
    .topbar {
      display: flex; align-items: center; justify-content: space-between;
      padding: 16px 28px; background: #1e293b; border-bottom: 1px solid #334155;
    }
    .brand { display: flex; align-items: center; gap: 12px; }
    .brand h1 { font-size: 18px; font-weight: 700; color: #f8fafc; }
    .dot { width: 10px; height: 10px; border-radius: 50%; background: #10b981; box-shadow: 0 0 8px #10b981; }
    .badge {
      background: rgba(56, 189, 248, 0.15); color: #38bdf8;
      padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;
    }
    .btn-update, .btn-install {
      background: #2563eb; color: #fff; border: none; border-radius: 8px;
      padding: 8px 16px; font-weight: 600; cursor: pointer; transition: 0.2s;
    }
    .btn-update:hover:not(:disabled) { background: #1d4ed8; }
    .btn-update:disabled, .btn-install:disabled { opacity: 0.6; cursor: not-allowed; }
    .btn-install { background: #10b981; margin-top: 10px; }
    .content { flex: 1; padding: 32px; max-width: 960px; margin: 0 auto; width: 100%; }
    .card {
      background: #1e293b; border: 1px solid #334155; border-radius: 14px;
      padding: 28px; box-shadow: 0 10px 25px rgba(0,0,0,0.3);
    }
    .card h2 { margin-bottom: 8px; color: #38bdf8; }
    .card p { color: #94a3b8; line-height: 1.6; }
    .alert {
      margin-top: 16px; padding: 12px 16px; border-radius: 8px;
      background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.3); color: #e2e8f0;
    }
    .update-box {
      margin-top: 16px; padding: 16px; border-radius: 10px;
      background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.35);
    }
  `]
})
export class AppComponent implements OnInit {
  private http = inject(HttpClient);

  version = signal<string>('v1.0.0');
  checking = signal<boolean>(false);
  updating = signal<boolean>(false);
  progress = signal<number>(0);
  statusMessage = signal<string>('');
  updateInfo = signal<{ version: string; download_url: string } | null>(null);

  ngOnInit() {
    this.http.get<any>('/api/system/version').subscribe({
      next: (res) => {
        if (res?.version) this.version.set('v' + res.version.replace(/^v/i, ''));
      },
      error: () => {}
    });
  }

  checkForUpdate() {
    this.checking.set(true);
    this.statusMessage.set('');
    this.http.post<any>('/api/system/update/check', {}).subscribe({
      next: (res) => {
        this.checking.set(false);
        if (res?.has_update) {
          this.updateInfo.set({ version: res.version, download_url: res.download_url });
          this.statusMessage.set(`Phát hiện bản cập nhật mới v${res.version}!`);
        } else {
          this.updateInfo.set(null);
          this.statusMessage.set('Bạn đang sử dụng phiên bản mới nhất.');
        }
      },
      error: (err) => {
        this.checking.set(false);
        this.statusMessage.set('Không thể kiểm tra cập nhật lúc này.');
      }
    });
  }

  installUpdate() {
    this.updating.set(true);
    this.statusMessage.set('Đang tải gói cài đặt từ GitHub Releases...');
    this.http.post<any>('/api/system/update/install', {}).subscribe({
      next: () => {
        this.statusMessage.set('Đang tiến hành cài đặt và khởi động lại...');
      },
      error: () => {
        this.updating.set(false);
        this.statusMessage.set('Lỗi khi tải hoặc cài đặt bản cập nhật.');
      }
    });
  }
}
