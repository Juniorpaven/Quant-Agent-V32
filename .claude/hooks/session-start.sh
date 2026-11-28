#!/bin/bash
# Hook khởi động phiên cho Claude Code trên cloud: (1) sửa tham chiếu git để hook "commit chưa đẩy" không báo nhầm trong clone nông,
# (2) cài thư viện Python cho backtest và kiểm thử. Chỉ chạy trên cloud, bỏ qua phần cài nếu requirements.txt không đổi.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

cd "${CLAUDE_PROJECT_DIR:-.}"

# --- (1) Tham chiếu git: clone nông chỉ lấy một nhánh nên thiếu origin/<nhánh>; thêm refspec đầy đủ và lấy nhánh hiện tại
if [ -d .git ] || git rev-parse --git-dir >/dev/null 2>&1; then
  if ! git config --get-all remote.origin.fetch | grep -qx '+refs/heads/\*:refs/remotes/origin/\*'; then
    git config --unset-all remote.origin.fetch 2>/dev/null || true
    git config --add remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'
  fi
  nhanh="$(git branch --show-current 2>/dev/null || true)"
  if [ -n "$nhanh" ]; then
    git fetch -q origin "$nhanh" 2>/dev/null || true
    if git rev-parse --verify -q "refs/remotes/origin/$nhanh" >/dev/null; then
      git branch --set-upstream-to="origin/$nhanh" "$nhanh" >/dev/null 2>&1 || true
    fi
  fi
fi

# --- (2) Thư viện Python (pip vào Python hệ thống; file băm nằm cùng thư mục gói để mất theo container)
if [ -f requirements.txt ]; then
  hashes="$(python3 -I -c 'import sysconfig; print(sysconfig.get_path("purelib"))')/.session-start.sha256"
  if ! sha256sum --check --status "$hashes" 2>/dev/null; then
    rm -f "$hashes"
    python3 -m pip install -q -r requirements.txt
    sha256sum .claude/hooks/session-start.sh requirements.txt > "$hashes" || rm -f "$hashes"
  fi
fi
