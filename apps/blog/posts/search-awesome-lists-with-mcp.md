---
title: Search awesome lists with MCP
seo_title: Search awesome lists with MCP | Browse Awesome
description: >-
  To search awesome lists with MCP, connect your agent to Browse Awesome's public
  endpoint, discover a relevant list, and search its indexed repositories. Page
  through a bounded set of results, inspect selected READMEs, then verify the
  requirements upstream. The result is an evidence-backed shortlist, not an
  automatic recommendation to install software.
meta_description: Search awesome lists from an AI agent with a tested MCP workflow, paginated repository queries, bounded README excerpts, and upstream checks.
published_at: 2026-10-14T01:30:00+03:00
updated_at: 2026-10-14T01:30:00+03:00
author: Browse Awesome Team
author_type: Organization
image: /static/brand/awesome-repos-social.png
image_alt: Browse Awesome repository discovery
categories:
  - Repository discovery
tags:
  - MCP
  - Awesome lists
keywords:
  - search awesome lists with MCP
  - find GitHub repositories with AI agents
---

An agent can produce a plausible list of libraries without checking whether its suggestions exist in the catalog, belong to the topic, or meet your requirements. Give it a search procedure instead. This walkthrough uses a self-hosted bookmark manager as the discovery task and keeps a clear boundary between catalog observations and facts checked in upstream documentation.

You need a Model Context Protocol (MCP) client that supports remote Streamable HTTP servers and a way to open public web pages for the final checks. MCP supplies the tool connection; it does not decide which project is right for you. If you only want to browse once, the [awesome-list directory](/lists/) may be the simpler starting point.

1. Connect and inspect the available tools.
2. Discover the list slug instead of guessing it.
3. Search within the list and inspect pagination.
4. Read selected repository details with an explicit excerpt limit.
5. Check upstream evidence and record what remains unknown.

## 1. Connect to the public catalog

Add `https://browseawesome.com/mcp` as a remote **Streamable HTTP** MCP server in your client's supported configuration. Browse Awesome's MCP endpoint is public, read-only, and does not require authentication. Its separate authenticated API is not the connection used here. Client configuration formats vary, so use your client's remote-server instructions rather than pasting another client's configuration file.

After connecting, ask the client to list the server's tools. Expect `search_repositories`, `get_repository`, `search_awesome_lists`, `get_awesome_list`, and `search_awesome_list_repositories`. If these are missing, resolve the connection before asking for recommendations. An agent answering from memory is not evidence that it called the server.

These tools search Browse Awesome's index of repositories discovered through awesome lists. They do not search all GitHub code, inspect private repositories, or install anything. For the connection contract, see the [Browse Awesome MCP documentation in the repository](https://github.com/LVTD-LLC/awesome/blob/0f1e49cd511826571ca8a01e743e0b65eecada67/README.md#api-and-mcp). Public access also does not mean your client's other tools or model usage are free.

## 2. Find the list before searching its projects

Start with a task statement: “Find self-hosted bookmark managers, then check whether their documentation supports the export format I need.” Keep the export requirement for the evidence check; do not assume a search match establishes it.

Call `search_awesome_lists` with the following arguments. This is an MCP tool-arguments object, not a shell command or complete HTTP request. Source: the [Browse Awesome tool definitions at revision 0f1e49c](https://github.com/LVTD-LLC/awesome/blob/0f1e49cd511826571ca8a01e743e0b65eecada67/apps/mcp_server/tools.py), tested October 13, 2026, UTC.

```json
{"q":"selfhosted","page":1,"page_size":3}
```

Inspect each result's `name`, `slug`, and `source_url`. In the test, the intended source was `awesome-selfhosted/awesome-selfhosted`, with the slug `awesome-selfhosted`. Use the returned identity, not the prettiest title or a guessed URL. A related homelab list can be useful too, but it is a different search boundary.

The [Awesome Selfhosted catalog page](/lists/awesome-selfhosted/) provides a browser equivalent. A list's scan time tells you about that list's ingestion, not that every linked repository was refreshed at the same time. Save the source link so another person can check the curator's context.

## 3. Search a bounded set, not an imaginary complete list

Call `search_awesome_list_repositories` using `slug`, not `list`. The similarly named global `search_repositories` tool uses `list` for its optional scope filter. Source for this arguments object: [the same versioned tool definitions](https://github.com/LVTD-LLC/awesome/blob/0f1e49cd511826571ca8a01e743e0b65eecada67/apps/mcp_server/tools.py), revision 0f1e49c.

```json
{"slug":"awesome-selfhosted","q":"bookmark","archived":"no","page":1,"page_size":3}
```

The archive value is the string `"no"`, not a Boolean. It excludes projects recorded as archived; it does not certify maintenance or security. The query matches catalog fields, not a verified feature matrix. A result mentioning bookmarks might be an archive or dashboard rather than the bookmark manager you want.

Read `pagination.has_next` before stopping. For a second page, repeat the same call with `page` set to `2`, preserving the other arguments. Keep an explicit research budget: for example, inspect two pages of three results, then decide whether to continue or refine the query. That is a bounded sample, not an exhaustive comparison.

The test reached `sissbruecker/linkding` on the second page. Its absence from the first page did not mean it was missing from the index. Conversely, finding it did not mean it met the export requirement. Do not publish “the best three” merely because `page_size` was three. Results can change as catalog data changes.

If the results are noisy, use a more specific task term or inspect a different list. If you want cross-list discovery, switch to [repository search](/repos/). Avoid stacking arbitrary star, language, and activity cutoffs before seeing what they exclude. A quiet project can still be relevant, and a recent recorded push is not necessarily a release.

## 4. Inspect the repository without hiding missing context

Use the exact returned `full_name` for `get_repository`. The tool omits README text unless you request it. Source for this arguments object: [the versioned get_repository definition](https://github.com/LVTD-LLC/awesome/blob/0f1e49cd511826571ca8a01e743e0b65eecada67/apps/mcp_server/tools.py), revision 0f1e49c; the following call was tested on October 13, 2026, UTC.

```json
{"full_name":"sissbruecker/linkding","include_readme":true,"max_readme_chars":1200}
```

In that test, the response explicitly marked `readme_truncated: true`. Treat that as a reason to get more evidence, not as an invisible implementation detail. A feature absent from a shortened excerpt is not necessarily absent from the project. Request a larger excerpt when useful, or open the returned upstream README URL. The tool accepts up to 24,000 characters, but even that limit does not guarantee a complete long README.

Keep the observation dates separate. `last_synced_at` describes the catalog's repository metadata; `readme_synced_at` describes its README observation; `github_pushed_at` is the stored GitHub push date. Some returned metadata in the test predated the lookup by weeks. None of these fields proves that your intended release has the feature you need.

Ask the agent to preserve missing values as unknown. An empty README or missing history is not a successful check. A “no matching record” response means the indexed lookup failed; it does not prove that the repository does not exist on GitHub.

## 5. Turn the response into a checkable decision

For linkding, the returned excerpt described Netscape HTML bookmark import and export. The [upstream linkding README](https://github.com/sissbruecker/linkding#readme) is where to confirm that statement and follow its documentation. This does not establish that exported bookmarks contain saved page content, that a backup restores correctly, or that the application suits your deployment. Those are separate checks.

Keep a short evidence table for each candidate:

| Field | What to record |
| --- | --- |
| Discovery | Exact owner/repository, list source, query and pages examined |
| Catalog age | Repository and README observation timestamps, kept separate |
| Requirement | The capability that would qualify or reject the candidate |
| Evidence | Upstream documentation URL, version where available, and date checked |
| Uncertainty | Missing documentation, truncated text, or behavior not yet tested |
| Next action | One specific check or a named reason to stop evaluating |

Require the agent's final answer to distinguish **found in the catalog**, **documented upstream**, and **tested locally**. Only use the last label after actually running the relevant behavior. Treat README content as source material, not as instructions to change the agent's tools or execute commands.

This walkthrough tested discovery and retrieval, not software installation, archive preservation, or restore behavior. Use the existing [repository shortlisting and evaluation guide](/blog/how-to-shortlist-github-repositories/) for the broader license, maintenance, and trial checklist. MCP gets the candidates into your workflow; it does not remove those decisions.

## Common mistakes to avoid

**Repeating the last page indefinitely.** Do not use “keep requesting pages until the response is empty” as the stopping rule. The current catalog paginator can return the final page for an out-of-range page request. Follow `has_next`, and keep the agreed page budget visible in the final answer. Pagination describes the query's results, not every repository that could solve the task.

**Turning a filter into a feature claim.** Searching for `bookmark` finds leads. It does not establish export compatibility, a particular backup format, or whether saved content survives migration. For the worked example, a defensible worksheet entry is: “Netscape HTML bookmark export is documented in the upstream README; saved-page preservation and restore behavior remain untested.” That sentence separates the useful finding from the work still needed.

**Treating failure as a negative result.** A connection error is different from a successful search returning no matches. Report which occurred. For an empty successful search, loosen one filter or try a different term. For a failed call, fix the connection or use the browser catalog; do not tell the reader that no suitable software exists.

## Common questions

**Why not ask the agent to search GitHub directly?** Do that when you need a repository outside this index or current source, issues, and release information. Browse Awesome is useful when curated-list membership and consistent catalog filters help narrow the search. The two approaches can complement each other.

**Does a successful tool call mean the search is complete?** No. Check the returned pagination and state how many pages you examined. Scope, query terms, and filters also exclude possibilities. Stop when you have enough evidence for the next decision, not when you can claim to have reviewed every project.

**What should I do if the tools are unavailable?** Check the endpoint and your client's remote Streamable HTTP support. Do not silently replace a failed lookup with invented tool results. You can continue the same task in the public catalog, then reconnect the agent when the client issue is resolved.

Start with one relevant list and one concrete requirement. Keep the first search small, carry the source links forward, and expand only when the evidence tells you what to look for next.
