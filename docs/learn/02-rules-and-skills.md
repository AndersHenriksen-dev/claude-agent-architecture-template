# 2. Rules and skills

Both are Markdown that ends up in the model's context. The difference is when, and what they are for.

## Rules

`CLAUDE.md` and the files in `.claude/rules/` are loaded by Claude Code. The docs are direct about their limits: Claude treats them "as context, not enforced configuration", and they point you to a `PreToolUse` hook if something must be blocked.

**Unscoped rule.** No frontmatter. Loads at launch, like `CLAUDE.md`.

**Path-scoped rule.** Frontmatter with `paths`. Loads when Claude uses the Read, Write or Edit tool on a matching file.

```markdown
---
paths:
  - "src/subfinder/lib/statement/**"
---

# Money
- Never use `float` for money.
```

**Writing one that gets followed.** Be concrete enough to check. "Never use `float` for money" works and "be careful with numbers" does not. The docs suggest under 200 lines per file, because longer files lower how well they are followed, and two rules that contradict each other get resolved arbitrarily.

## Every place instructions can live

`CLAUDE.md` is not one file. Claude Code looks in several places:

| File | Who it is for | When it loads |
|---|---|---|
| `~/.claude/CLAUDE.md` | You, in every project | At launch |
| `CLAUDE.md` or `.claude/CLAUDE.md` | Everyone on the project, through git | At launch |
| `CLAUDE.local.md` | You, in this project. Add it to `.gitignore` | At launch |
| A parent folder's `CLAUDE.md` | Whoever starts below it | At launch |
| A subfolder's `CLAUDE.md` | Whoever works there | When Claude reads or edits a file in that subfolder |

**They stack.** Claude Code does not pick one. It joins them from the top of the folder tree down, so the closest is read last, and in each folder `CLAUDE.local.md` comes after `CLAUDE.md`. Being read last is not a guarantee of winning: if two files contradict each other, Claude may pick either.

**Subfolder files save context.** This repo's [lib/hooks/CLAUDE.md](../../src/subfinder/lib/hooks/CLAUDE.md) says what to keep in mind when editing hooks. Anyone working on the statement never pays for it.

**A subfolder `CLAUDE.md` or a path-scoped rule?** Both load on demand. Use the subfolder file when the instructions are about one folder. Use a rule when they follow a kind of file across folders: `money.md` here covers `lib/statement/`, `config/statement/` and `tests/statement/`.

**`CLAUDE.local.md` is for what is true only for you**, such as your sandbox URL or your preferred test data. It stays out of git only if you add it to `.gitignore`, and it exists only in the worktree where you made it.

**Comments for people.** Block-level HTML comments are stripped before the text reaches the model, so you can leave notes for maintainers at no cost in context.

To see what loaded in a session, run `/context all`.

## Skills

A skill is a folder:

```text
.claude/skills/find-subscriptions/
|-- SKILL.md            required: frontmatter, then steps
`-- summary-format.md   read only if the steps send Claude there
```

Skills load in three stages, called **progressive disclosure**:

| Stage | When | What loads |
|---|---|---|
| 1 | Startup | The `name` and `description` |
| 2 | When used | The body of `SKILL.md` |
| 3 | If needed | Other files it points to. A script's code never loads, only its output |

**The description does the routing.** The model reads it to decide whether to use the skill, so it must say what the skill does and when to use it. A vague description means a skill that never fires.

**You can also call it yourself**, with `/find-subscriptions`. `disable-model-invocation: true` makes a skill manual only, which suits anything with side effects you want to trigger by hand.

**`allowed-tools` pre-approves. It does not restrict.** A skill with `allowed-tools: Read` can still try `Bash`, and that call goes through the normal permission check. To remove a tool, use `disallowed-tools`.

## Telling them apart

| | Rule | Skill |
|---|---|---|
| Shape | Facts and standards | Steps |
| Applies | Throughout the work | During one kind of task |
| When it loads | At launch, or on a matching file | When used |
| Test | "Should Claude know this while doing something else?" | "Would I paste this when starting a task?" |

In this repo, "a negative amount is money out" is a rule: it is true whenever you touch statement code. "List the lines, group by merchant, tag, save a summary" is a skill: it only makes sense when someone asks for the job.

When a section of `CLAUDE.md` starts to read as numbered steps, move it into a skill. The docs recommend the same.

## Testing what is not code

Python never imports these files, so a broken one fails silently: the rule never loads, or the skill never fires. The tests here catch what a program can check: the frontmatter parses, the name meets the documented limits, every tool the skill names exists on the server, every linked file exists, and every path pattern matches a real file. They cannot show the model follows the text. That takes a real run.

One more trick: when part of a rule can be checked by a machine, also write the check. The money rule says no `float`, and a test walks the syntax tree of the statement code to confirm it.

## Where to find this in the code

- The rules: [money.md](../../.claude/rules/money.md) and [no-advice.md](../../.claude/rules/no-advice.md).
- The skill: [SKILL.md](../../.claude/skills/find-subscriptions/SKILL.md) and [summary-format.md](../../.claude/skills/find-subscriptions/summary-format.md).
- Reading them from Python: [project_files.py](../../src/subfinder/lib/demo/project_files.py). The tests: [test_project_files.py](../../tests/demo/test_project_files.py).
