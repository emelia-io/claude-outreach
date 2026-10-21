# Setup

Fifteen minutes, most of which is waiting for an API key page to load. You need
Claude Code. Everything else is optional until you want to enrich or send.

1. [Install the plugin](#1-install-the-plugin)
2. [Get your Emelia API key](#2-get-your-emelia-api-key)
3. [Set the keys as environment variables](#3-set-the-keys-as-environment-variables)
4. [Connect the MCP server, no key needed](#4-connect-the-mcp-server-no-key-needed)
5. [Check it works](#5-check-it-works)
6. [Add Basile, optional](#6-add-basile-optional)
7. [The one thing to know before your first campaign](#7-the-one-thing-to-know-before-your-first-campaign)
8. [Rate limits](#8-rate-limits)
9. [Running with no keys at all](#9-running-with-no-keys-at-all)
10. [When something does not work](#10-when-something-does-not-work)

## 1. Install the plugin

```
/plugin marketplace add emelia-io/claude-outreach
/plugin install claude-outreach@claude-outreach
```

Restart Claude Code, then type `/outreach` and check that it answers.

Manually instead, into your user skills directory:

```bash
git clone https://github.com/emelia-io/claude-outreach.git
cp -r claude-outreach/skills/* ~/.claude/skills/
cp -r claude-outreach/agents/* ~/.claude/agents/
```

Windows PowerShell:

```powershell
git clone https://github.com/emelia-io/claude-outreach.git
Copy-Item -Recurse claude-outreach\skills\* $HOME\.claude\skills\
Copy-Item -Recurse claude-outreach\agents\* $HOME\.claude\agents\
```

Copy the agents too. Without them the skills still work, they just do the fan-out
steps (sourcing, enrichment, copy variants, mailbox audits) one item at a time.

## 2. Get your Emelia API key

[app.emelia.io/settings/api](https://app.emelia.io/settings/api), create a key,
copy it once. It is shown once.

Rather not handle a key? Go to [section 4](#4-connect-the-mcp-server-no-key-needed):
the MCP server signs you in with your Emelia account, and the skills use it first. The
key stays what the bundled scripts need, and what CI or a machine without a browser
needs.

You need an Emelia account for anything that finds an email, verifies an address,
finds a mobile, creates a campaign or reads replies. The rest of the pipeline runs
without one.

## 3. Set the keys as environment variables

macOS and Linux, in `~/.zshrc` or `~/.bashrc`:

```bash
export EMELIA_API_KEY="..."      # enrichment, contacts, campaigns, replies
export BASILE_API_KEY="..."      # optional, French B2B data
```

Windows PowerShell, permanently:

```powershell
setx EMELIA_API_KEY "..."
setx BASILE_API_KEY "..."
```

Open a new terminal so the variables exist, then start Claude Code from it. A key
set in a shell that Claude Code was not launched from is not visible to it, which is
the most common false alarm on this page.

Never put a key in a file inside a repository. If you already did, rotate it in the
Emelia app before anything else.

## 4. Connect the MCP server, no key needed

The MCP server covers the whole Emelia API except the legacy campaigns, plus what the
REST API does not offer: campaign statistics (`get_campaign_stats`), warmup state
(`get_warmup_status`, `set_warmup`), sending accounts (`list_email_providers`), list
management (`create_list`, `list_lists`, `get_list`, `rename_list`, `delete_list`,
`get_list_contacts`, `update_contact`, `delete_contact`), `find_contact`, which looks a
contact up across every list in the account, LinkedIn extractions
(`create_linkedin_scraper`) and, once the Inbox is open in Emelia, the inbox. When it
is connected, the skills use it first.

Without it and without a key, `/outreach deliverability` cannot read your warmup state
and says so rather than assuming it is fine.

**Sign in with your Emelia account** (recommended, nothing to copy):

```bash
claude mcp add --transport http --scope user emelia https://mcp.emelia.io/mcp
```

Then run `/mcp` in Claude Code, pick `emelia` and choose **Authenticate**. Your
browser opens an Emelia page: check the account shown and click **Authorize**. Ask
"list my campaigns" to test it. The access token stays inside Claude Code: the
skills reach Emelia through the MCP tools, and the bundled scripts, which call the
REST API directly, still need `EMELIA_API_KEY`.

For a project shared with a team, the same in a `.mcp.json` at its root. It holds no
secret, and each person signs in with their own account:

```json
{
  "mcpServers": {
    "emelia": {
      "type": "http",
      "url": "https://mcp.emelia.io/mcp"
    }
  }
}
```

**Or with your API key** (CI, scripts, a machine without a browser). Claude Code then
does not ask you to sign in:

```bash
claude mcp add --transport http emelia https://mcp.emelia.io/mcp \
  --header "Authorization: $EMELIA_API_KEY" \
  --scope user
```

Or in a `.mcp.json`:

```json
{
  "mcpServers": {
    "emelia": {
      "type": "http",
      "url": "https://mcp.emelia.io/mcp",
      "headers": { "Authorization": "${EMELIA_API_KEY}" }
    }
  }
}
```

Three things about that file. Use `${EMELIA_API_KEY}` rather than the key itself, so
the file is safe to commit. Keep the server named `emelia`: the agents list their
MCP tools as `mcp__emelia__<tool>`, and another name stops those entries matching.
And the server accepts the key as a raw `Authorization` header, as
`Authorization: Bearer <key>`, or as `X-Api-Key`, so any of the three works if your
client insists on one.

Check it responds at all, no key needed:

```bash
curl -s https://mcp.emelia.io/mcp/health
# {"ok":true}
```

The server is stateless and answers `POST /mcp` only. A `GET` or `DELETE` on `/mcp`
returns 405 with "this MCP server is stateless, use POST /mcp", which is the server
working, not a broken configuration.

Then, in Claude Code, `/mcp` should list `emelia` as connected.

Two notes. If Emelia is already connected as a connector of your Claude account, its
tools can show up in Claude Code under another prefix: the skills find them by the end
of their name, but the agents, which list `mcp__emelia__<tool>`, do not, so add the
server as above as well. And the plugin does not declare the server itself, on
purpose: a server shipped inside a plugin gets its tools renamed
`mcp__plugin_claude-outreach_emelia__<tool>`, and it would sit next to the `emelia`
server you may already have, with every tool twice.

## 5. Check it works

The fastest honest test is a REST call that costs nothing:

```bash
curl -s -o /dev/null -w '%{http_code}\n' https://api.emelia.io/advanced/campaigns \
  -H "Authorization: $EMELIA_API_KEY"
```

`200` means the key works. `401` means it does not: it was mistyped, it was revoked,
or the variable is empty in this shell (`echo $EMELIA_API_KEY` and look).

Then, in Claude Code:

```
/outreach deliverability
```

It reads your sending domains and mailboxes and spends nothing. If it reports what
it found, the setup is done.

## 6. Add Basile, optional

Only useful if you sell in France. Base `https://api.basile.cc`, header
`Authorization` with the **raw key, no `Bearer` prefix**. Full reference at
[docs.basile.cc](https://docs.basile.cc), and what it is good for is in
[DATA-SOURCES.md](DATA-SOURCES.md).

Counting is free and unlimited, so the check costs nothing:

```bash
curl -s https://api.basile.cc/companies/find \
  -H "Authorization: $BASILE_API_KEY" -H "Content-Type: application/json" \
  -d '{"countOnly":true,"filters":{"headquarters_city":{"include":["Lyon"]},"company_ceased":false}}'
```

You should get a `total` and an empty `leads` array. Extracting records is what
costs: 1 credit per record returned, billed on every call.

## 7. The one thing to know before your first campaign

**The whole campaign is built through the API, and nothing starts without your yes.**
`POST /advanced/campaigns` creates it, always as an advanced campaign, whether it sends
email, LinkedIn messages or both. The steps, delays, schedule, list and sending
accounts are then set by API, and so is the start. Two things stay in the Emelia app:
connecting a mailbox or a LinkedIn account, and the subscription a campaign needs to
start.

So the working order is:

1. The skills produce the sequence spec, the copy and the cleaned list.
2. `/outreach campaign` builds the campaign from them, runs the pre-flight, and starts
   it only after your explicit yes, unless you would rather press Launch in the app.
3. The skills push contacts into the list attached to that campaign. Every contact
   added enters the running campaign on its own.

That third step is what keeps it going. Once the campaign exists and runs, feeding it
is a one line operation and you never touch the interface again.

## 8. Rate limits

Per minute, per key, on a rolling sixty second window:

| Plan | Requests per minute |
|---|---|
| No subscription | 30 |
| Start | 100 |
| Grow | 300 |
| Scale | 1,000 |

Over the limit the API answers `429` and the message says the maximum for your plan.

Polling counts against it. An enrichment is one POST plus one GET every two seconds
until the job finishes, so a slow row can cost fifteen requests. Divide your limit by
fifteen for a safe number of rows in flight: 2 with no subscription, 6 on Start, 20
on Grow, 60 on Scale. That is arithmetic on the published limit, not a measurement,
and the enrichment agent already paces itself this way.

## 9. Running with no keys at all

Supported, and useful. Without `EMELIA_API_KEY`, these still work completely:
`/outreach offer`, `/outreach icp`, `/outreach leads` from Basile or a CSV,
`/outreach filter`, `/outreach write`, `/outreach personalize`, `/outreach sequence`,
and `/outreach audit` on `outreach/sequence.md`.

Everything that touches Emelia runs in dry run: it produces its file, states which
calls it would have made and what they would have cost, and changes nothing. It is a
good way to price a campaign before buying anything.

## 10. When something does not work

[TROUBLESHOOTING.md](TROUBLESHOOTING.md) covers the failures people actually hit: a
key that is refused, a quota that is exhausted, an enrichment job that never
finishes, a campaign that will not start, emails landing in spam, variables that
render empty in a sent email, and a list that comes back empty after filtering.
