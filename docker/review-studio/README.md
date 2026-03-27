# Review Studio

Review Studio is a reusable code review toolkit for teams that want review comments written with the tone and rigor of a senior enterprise architect or principal engineer.

It is designed for:

- Java code
- Python code
- Kubernetes YAML
- local repositories
- pasted code snippets
- unified diffs from pull requests
- Bitbucket-ready comment payload generation

## What it does

Review Studio applies a deterministic rule set and formats comments in one of three personas:

- `architect`: high-level design, coupling, scalability, operational risk
- `engineer`: correctness, maintainability, runtime and failure behavior
- `test`: coverage gaps, determinism, edge cases, regression prevention

The tool can:

- review a single file or pasted code
- review a local repository checkout
- review a unified diff file
- emit markdown, JSON, or Bitbucket Cloud comment payloads
- optionally publish findings to a Bitbucket Cloud pull request

## Quick start

### Local Python

```bash
cd docker/review-studio
sh ./review-studio review-repo --repo /path/to/project --persona architect --format markdown
```

### Without install

```bash
cd docker/review-studio
PYTHONPATH=src python3 -m review_studio.cli review-repo --repo /path/to/project --persona engineer
```

### Docker

```bash
cd docker/review-studio
docker build -t fq-review-studio:0.1.0 .
docker run --rm -v /path/to/project:/workspace/project fq-review-studio:0.1.0 \
  review-repo --repo /workspace/project --persona architect --format markdown
```

## Example commands

### Review a single file

```bash
sh ./review-studio review-code \
  --file /path/to/Foo.java \
  --persona architect \
  --format markdown
```

### Review a pasted snippet

```bash
printf 'try:\\n    pass\\nexcept:\\n    pass\\n' | \
sh ./review-studio review-code \
  --stdin \
  --language python \
  --persona engineer \
  --format markdown
```

### Review a pull request diff

```bash
git diff origin/main...HEAD > /tmp/pr.diff
sh ./review-studio review-diff \
  --diff-file /tmp/pr.diff \
  --persona test \
  --format markdown
```

### Create Bitbucket comment payloads

```bash
sh ./review-studio review-diff \
  --diff-file /tmp/pr.diff \
  --persona architect \
  --format bitbucket \
  --output /tmp/review-comments.json
```

### Publish to Bitbucket Cloud

```bash
export BITBUCKET_USERNAME=your-user
export BITBUCKET_APP_PASSWORD=your-app-password

sh ./review-studio publish-bitbucket \
  --workspace your-workspace \
  --repo-slug your-repo \
  --pull-request 42 \
  --findings-file /tmp/review-comments.json
```

## Review method

Review Studio is opinionated:

1. correctness first
2. architecture and blast radius second
3. operational safety third
4. tests and regression prevention throughout

This is not a style linter. It looks for production-impacting review topics such as:

- broad exception handling
- mutable defaults
- shell injection risk
- unsafe YAML loading
- unbounded threading without shutdown
- Kubernetes workloads missing probes or resource controls
- suspicious `latest` images
- TODO and FIXME markers in changed code
- maintainability hotspots that make enterprise support harder

## Bitbucket notes

- Inline publishing is implemented for Bitbucket Cloud pull request comments.
- For Bitbucket Server or Data Center, use `--format bitbucket` to generate comment payloads and adapt the publisher endpoint if your instance differs.

## Files

- `src/review_studio/`: core implementation
- `tests/`: unit tests
- `examples/bitbucket-pipelines.yml`: CI example

## Running tests

```bash
cd docker/review-studio
PYTHONPATH=src python3 -m unittest discover -s tests -v
```
