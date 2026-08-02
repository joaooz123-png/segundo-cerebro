# GitHub Copilot agents for the PF-ILD/PPF review

The repository defines project-level custom agents in `.github/agents/`. GitHub loads repository agents from the default branch. They can be selected in GitHub Copilot Agents, assigned to compatible issues, invoked from Copilot CLI, or inferred from the task description when cloud agent access is enabled.

## Agent catalog

### PF-ILD Review Orchestrator

Use for multi-stage tasks, work planning, reconciliation of outputs, or coordinating several specialists.

Example:

> Use the PF-ILD Review Orchestrator to plan the Embase import, assign specialist checks, and produce an auditable integration report without changing final eligibility decisions.

### PF-ILD Search Librarian

Use for database strategies, source coverage, book/chapter searches, registry searches, citation chasing, and search-log audits.

Example:

> Use the PF-ILD Search Librarian to translate the master concept strategy for Embase and prepare a PRESS-style audit and search-log entry.

### PF-ILD Deduplication and Family Linker

Use for duplicate candidates, identifier conflicts, and linking trial registrations, protocols, abstracts, primary reports, extensions, corrections, letters, and secondary analyses.

Example:

> Use the PF-ILD Deduplication and Family Linker to assess the INBUILD cluster. Do not delete records or change PRISMA counts; return recommendations for human confirmation.

### PF-ILD High-Recall Screener

Use for conservative title/abstract or full-text recommendations.

Example:

> Use the PF-ILD High-Recall Screener on this batch. Preserve reviews, guidelines, abstracts, books, and correspondence in the bibliographic corpus. Leave final decisions unresolved.

### PF-ILD Metadata and Vancouver Curator

Use for complete authorship, identifiers, books/chapters, journal abbreviations, corrections, retractions, and Vancouver references.

Example:

> Use the PF-ILD Metadata and Vancouver Curator to verify every author and format the references. Keep the full author list in structured data and use six authors plus et al. only in rendered Vancouver output.

### PF-ILD Lawful Full-Text Retriever

Use for access-status tracking and lawful retrieval routes.

Example:

> Use the PF-ILD Lawful Full-Text Retriever to locate lawful versions of the unresolved reports and record the exact version, URL, access status, and next step.

### PF-ILD Methodology and PRISMA Auditor

Use before merging imports, changing counts, circulating methods, or beginning synthesis.

Example:

> Use the PF-ILD Methodology and PRISMA Auditor to inspect the PubMed snapshot, seed reconciliation, and record-report-study accounting. Classify findings by severity and do not repair raw data silently.

## Recommended issue workflow

1. Create a narrowly scoped issue with inputs, expected files, and acceptance criteria.
2. In GitHub Copilot Agents, select the repository and the appropriate agent.
3. Assign the issue or paste the task into the selected agent session.
4. Require a pull request rather than direct default-branch edits.
5. Review provenance, unresolved uncertainty, and proposed human decisions.
6. Merge only after methodological or metadata audit when counts or evidence records change.

## Important limitations

- Agent profiles do not themselves schedule work.
- They do not override repository permissions or Copilot policy settings.
- Availability requires a paid Copilot plan and Copilot cloud agent enabled for the repository/account.
- GitHub.com currently ignores IDE-specific `handoffs`; orchestration uses agent inference or explicit subagent invocation instead.
- Human confirmation remains mandatory for eligibility, duplicate status, family linkage, and PRISMA changes.
