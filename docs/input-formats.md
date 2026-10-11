# Input formats for `fiverr-gig audit`

The audit accepts three file types. All produce the same result.

## JSON (also the format `/fiverr-optimize` writes)

A single gig object, a list of gigs, or a full `gig-config.json` with a `gigs` list (every gig is audited). Accepted keys:

| Key                    | Aliases           | Notes                                                                            |
| ---------------------- | ----------------- | -------------------------------------------------------------------------------- |
| `title`                |                   | string                                                                           |
| `category`             | `cat`             | optional                                                                         |
| `tags`                 |                   | list, or one comma-separated string                                              |
| `description`          | `desc`            | string                                                                           |
| `packages`             | `pricing`         | object with `basic`, `standard`, `premium`                                       |
| `packages.*.price`     |                   | number or "$1,200"                                                               |
| `packages.*.days`      | `delivery`, `del` | number, or text such as "3 days"                                                 |
| `packages.*.revisions` | `rev`             | optional                                                                         |
| `packages.*.items`     |                   | list of deliverables                                                             |
| `faq`                  |                   | list of `{q, a}` (or `question` / `answer`)                                      |
| `requirements`         |                   | list of strings                                                                  |
| `images`               |                   | list of `{type: image\|video\|pdf, width, height}`; omit to skip the image check |

See `examples/strong-gig.json`.

## YAML

Same keys as JSON. Needs PyYAML: `pip install "fiverr-gig-optimizer[yaml]"`.

## Markdown

```markdown
Title: I will build n8n automations to connect your tools
Category: Programming & Tech
Tags: n8n automation, workflow automation, n8n developer

## Description

Free text. Bullets start with "-".

## Packages

- basic: $60 | 3 days | 2 revisions | 1 workflow; 2 integrations
- standard: $150 | 5 days | 3 revisions | 3 workflows; error handling
- premium: $320 | 9 days | 5 revisions | full system; walkthrough video

## FAQ

Q: Which tools can you connect?
A: Anything with an API or webhook.

## Requirements

- Please describe the process step by step.

## Images

- image: 1280x769
- video
- pdf
```

See `examples/needs-work-gig.md`.
