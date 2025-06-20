@echo off
REM Remove executable bit from all .sh files in current directory (for git)
for %%f in (*.sh) do (
    git update-index --chmod=-x "%%f"
)
echo Removed executable bit from .sh files