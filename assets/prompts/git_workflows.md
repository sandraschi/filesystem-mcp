# Git Workflows — moved to git-github-mcp
Git operations (`clone`, `status`, `commit`, `branch`, `push`/`pull`) live in
git-github-mcp (`gitops:git_core` / `github_ops`). No git tools are registered
in filesystem-mcp; `get_help` for `repo_ops` / `git_*` returns a `moved` redirect.
