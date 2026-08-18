# Git Path Doctor

**当 Git 沉默时，直接问它“为什么”。**

Git Path Doctor 用一条命令解释某个路径为什么被跟踪、被忽略、从 `git status` 中“消失”、未出现在稀疏检出中，或在不同系统上表现异常。

它把 `git status --porcelain=v2`、`git check-ignore -v`、`git check-attr`、`git ls-files -v --stage`、索引标志和路径历史等分散证据汇总成可读报告。

```console
$ git-path-doctor explain build/debug.log
Path:  build/debug.log
State: IGNORED
Why:   An ignore rule excludes this untracked path.
Disk:  file
Index: not tracked
Ignore: .gitignore:14 -> *.log
```

## 适用场景

- `git add` 像是没有理会某个文件；
- 文件已经被跟踪，却又命中了 `.gitignore`；
- 文件确实修改了，但普通 `git status` 看不到；
- 稀疏检出没有把某个已跟踪路径放进工作区；
- 合并后留下了不易察觉的索引阶段；
- 仓库中的路径在 Windows/macOS 等大小写不敏感文件系统上冲突。

## 安装

需要 Python 3.10 或更高版本以及 Git。运行时没有第三方 Python 依赖，不联网、不上传数据。

```bash
python -m pip install "git-path-doctor @ git+https://github.com/cuijialin8888-code/git-path-doctor.git@v0.1.0"
git-path-doctor explain path/to/file
```

也可以使用 `pipx` 隔离安装：

```bash
pipx install "git+https://github.com/cuijialin8888-code/git-path-doctor.git@v0.1.0"
```

## 用法

解释一个或多个路径：

```bash
git-path-doctor explain .env src/app.py generated/output.bin
git-path-doctor --repo ../another-repo explain config/local.toml
git-path-doctor explain src/app.py --json
```

扫描整个仓库中容易隐藏状态的索引标志、未解决冲突和大小写碰撞：

```bash
git-path-doctor scan
git-path-doctor scan --json
git-path-doctor scan --fail-on error
```

默认扫描只报告信息并返回退出码 `0`。在持续集成中，可以用 `--fail-on warning` 或 `--fail-on error` 把对应严重度变成退出码 `10`。

报告会给出证据和谨慎的下一步建议，但不会执行建议命令。

## 安全边界

- 所有 Git 查询均为只读；
- 路径必须位于已发现的工作树内；
- 不读取文件内容、差异、环境变量、凭据或远程仓库；
- 不修改 `.gitignore`、`.gitattributes`、Git 索引或工作区文件；
- 不恢复文件、不清除标志、不暂存改动、不解决冲突；
- 无遥测、无网络请求。

项目定位不是替代 `git status` 或完整 Git 教程，而是把“这个路径为什么这样”解释清楚。

更完整的功能、退出码、JSON 结构和开发说明请查看[英文 README](README.md)、[工作原理](docs/how-it-works.md)与[安全说明](SECURITY.md)。

## 许可证

MIT
