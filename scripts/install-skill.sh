#!/usr/bin/env bash
# 단일 스킬을 사용자 기본 위치(Claude / Codex)에 설치합니다.
# 설치는 심볼릭 링크로 이루어지므로 저장소를 git pull 하면 변경 사항이 즉시 반영됩니다.
set -euo pipefail

# Claude Code / Codex 의 기본 스킬 디렉터리 (환경 변수로 재정의 가능)
CLAUDE_SKILLS_DIR=${CLAUDE_SKILLS_DIR:-"$HOME/.claude/skills"}
CODEX_SKILLS_DIR=${CODEX_SKILLS_DIR:-"$HOME/.codex/skills"}

usage() {
  cat >&2 <<'EOF'
Usage: install-skill.sh <skill-name> [--both|--claude-only|--codex-only]

  <skill-name>     skills/ 아래의 스킬 폴더 이름
  --both           Claude 와 Codex 양쪽에 설치 (기본값)
  --claude-only    ~/.claude/skills 에만 설치
  --codex-only     ~/.codex/skills 에만 설치

환경 변수 CLAUDE_SKILLS_DIR / CODEX_SKILLS_DIR 로 설치 경로를 재정의할 수 있습니다.
EOF
  exit 2
}

[[ $# -ge 1 && $# -le 2 ]] || usage

skill_name=$1
mode=${2:---both}
repo_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
source_dir="$repo_root/skills/$skill_name"

[[ -f "$source_dir/SKILL.md" ]] || {
  echo "알 수 없는 스킬입니다: $skill_name" >&2
  echo "사용 가능한 스킬:" >&2
  for d in "$repo_root"/skills/*/SKILL.md; do
    [[ -f "$d" ]] && echo "  - $(basename "$(dirname "$d")")" >&2
  done
  exit 1
}

link_skill() {
  local label=$1
  local target_root=$2
  local target="$target_root/$skill_name"

  mkdir -p "$target_root"
  if [[ -e "$target" && ! -L "$target" ]]; then
    echo "건너뜀: $target 이(가) 심볼릭 링크가 아닌 실제 파일/폴더라서 덮어쓰지 않습니다." >&2
    return 1
  fi
  ln -sfn "$source_dir" "$target"
  echo "[$label] 링크 생성: $target -> $source_dir"
}

case "$mode" in
  --both)
    link_skill "Claude" "$CLAUDE_SKILLS_DIR"
    link_skill "Codex"  "$CODEX_SKILLS_DIR"
    ;;
  --claude-only)
    link_skill "Claude" "$CLAUDE_SKILLS_DIR"
    ;;
  --codex-only)
    link_skill "Codex" "$CODEX_SKILLS_DIR"
    ;;
  *) usage ;;
esac
