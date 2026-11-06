# 9. Further reading

The docs change often, so read them over any summary, including this guide.

## Choosing between the types

- [Extend Claude Code](https://code.claude.com/docs/en/features-overview): Anthropic's own map of skills, hooks, MCP, subagents and plugins.
- [Building effective agents](https://www.anthropic.com/engineering/building-effective-agents): why to start with the simplest tier, and when an agent earns its cost.

## Rules and skills

- [How Claude remembers your project](https://code.claude.com/docs/en/memory): `CLAUDE.md`, `.claude/rules/`, path scoping, and how to write instructions that get followed.
- [Extend Claude with skills](https://code.claude.com/docs/en/skills): the file format and every frontmatter field.
- [Agent Skills overview](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview): progressive disclosure, and how skills differ per surface.
- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices): writing a description that fires.
- [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills): the design thinking behind them.

## Hooks, settings and permissions

- [Settings files and precedence](https://code.claude.com/docs/en/settings): which file to use, who it affects, and which value wins.
- [Claude directory reference](https://code.claude.com/docs/en/claude-directory): every file Claude Code reads.
- [Hooks reference](https://code.claude.com/docs/en/hooks): every event, its JSON, and its decision fields.
- [Hooks guide](https://code.claude.com/docs/en/hooks-guide): worked examples.
- [Configure permissions](https://code.claude.com/docs/en/permissions): the evaluation order, and how hooks and rules interact.

## MCP and connectors

- [Connect Claude Code to tools via MCP](https://code.claude.com/docs/en/mcp): `.mcp.json`, scopes and transports.
- [Model Context Protocol](https://modelcontextprotocol.io): the protocol itself.
- [MCP connector](https://platform.claude.com/docs/en/agents-and-tools/mcp-connector): the Messages API's `mcp_servers` and `mcp_toolset`, and every validation rule.
- [Building custom connectors via remote MCP servers](https://support.claude.com/en/articles/11503834-building-custom-connectors-via-remote-mcp-servers): the claude.ai side.

## The API

- [Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview): the loop this repo avoids, and when you need it.
- [Structured outputs](https://platform.claude.com/docs/en/build-with-claude/structured-outputs): how the schema is enforced.
- [Effort](https://platform.claude.com/docs/en/build-with-claude/effort): the control for how hard the model works.
- [Refusals and fallback](https://platform.claude.com/docs/en/build-with-claude/refusals-and-fallback): the `fallbacks` parameter and how it is billed.

## Running agents elsewhere

- [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview): Claude Code as a library. It reads this repo's `.claude/` folder.
- [Managed Agents overview](https://platform.claude.com/docs/en/managed-agents/overview): Anthropic runs the loop and a sandbox.

## Related in this portfolio

- [agent-injection-tests](https://github.com/AndersHenriksen-dev/agent-injection-tests): measures how far a prompt defense gets against a check in code. The argument for hooks, with numbers.
