#!/usr/bin/env bash
# 저장소의 모든 스킬을 사용자 기본 위치(Claude / Codex)에 설치합니다.
#
# 사용법:
#   ./scripts/install.sh                # 모든 스킬을 Claude + Codex 에 설치 (기본값)
#   ./scripts/install.sh --claude-only  # Claude 에만 설치
#   ./scripts/install.sh --codex-only   # Codex 에만 설치
set -euo pipefail

repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
mode=${1:---both}
found=0

for skill_dir in "$repo_root"/skills/*; do
  [[ -d "$skill_dir" && -f "$skill_dir/SKILL.md" ]] || continue
  found=1
  "$repo_root/scripts/install-skill.sh" "$(basename "$skill_dir")" "$mode"
done

[[ $found -eq 1 ]] || {
  echo "설치할 스킬을 찾지 못했습니다: $repo_root/skills" >&2
  exit 1
}

echo "완료되었습니다."
