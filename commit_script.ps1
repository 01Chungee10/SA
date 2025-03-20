# commit_script.ps1

# 대상 폴더로 이동
Set-Location -Path "C:\Users\kvm-user\SA"

# Git 저장소 초기화 여부 확인 (.git 폴더 존재 여부)
if (-not (Test-Path ".git")) {
    Write-Host "Git 저장소가 아닙니다. 저장소를 초기화합니다..."
    git init
    git remote add origin https://github.com/01Chungee10/SA.git
}

# 모든 변경사항 스테이징
git add .

# 커밋 메시지 지정 (인자로 전달받은 메시지가 있으면 사용, 없으면 기본 메시지 사용)
if ($args.Count -gt 0) {
    $commitMsg = $args[0]
} else {
    $commitMsg = "자동 커밋: 전체 변경사항 반영"
}
git commit -m "$commitMsg"

# 원격 저장소로 push (기본 브랜치가 master인 경우)
git push -u origin master
