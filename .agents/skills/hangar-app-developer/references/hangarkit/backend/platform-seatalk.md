# Platform SeaTalk groups

ID: `backend.platform.seatalk`
Category: `backend`

Create and manage SeaTalk groups through platform-owned bots, without SeaTalk bot credentials or app integration configuration.

## Import

`from hangarkit.platform import seatalk`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `seatalk.create_group(group_name, member_emails=None, member_seatalk_ids=None, owner_email=None, message=None, send_ping_msg=False, timeout=30)`
- `seatalk.list_groups(query=None, limit=50, timeout=30)`
- `seatalk.get_group(infrabot_group_id, timeout=30)`
- `seatalk.get_group_members(infrabot_group_id, timeout=30)`
- `seatalk.add_group_members(infrabot_group_id, member_emails, mention_members=False, timeout=30)`
- `seatalk.send_group_message(infrabot_group_id=None, message, thread_id=None, timeout=30, group_id=None)`

## Details

Use `hangarkit.platform.seatalk` for group operations performed by platform-owned SeaTalk bots. Group creation, discovery, lookup, and membership use [InfraBot](https://link.seatalk.io/profile/open?seatalk_id=1352620613). `send_group_message()` ensures the Toolverse SOP bot is in the InfraBot-managed group and sends only through that SOP bot. These helpers never use an app's configured SeaTalk bot, and apps must not provide a bot ID, secret, callback signature, requester email, or bot type. Group creation may provide `owner_email`; when omitted, Hangar uses the current runtime user's email.

Every `infrabot_group_id` in this module is the numeric **InfraBot group ID** used by SPACE/Toolverse. It is not SeaTalk's official string group ID. `create_group()` returns this ID as `result["infrabot_group_id"]`; it also retains `result["group_id"]` as a compatibility alias for existing apps.

For a group created outside this helper, add [InfraBot](https://link.seatalk.io/profile/open?seatalk_id=1352620613) to the SeaTalk group before calling `get_group_members()`, `add_group_members()`, or `send_group_message()`. If InfraBot is absent, the operation fails with guidance to add it.

## Function inputs

- `create_group(group_name, member_emails=None, member_seatalk_ids=None, owner_email=None, message=None, send_ping_msg=False, timeout=30)`
  - `group_name` is required.
  - Provide at least one email in `member_emails` or one positive integer SeaTalk ID in `member_seatalk_ids`.
  - SeaTalk IDs are intended for bot or service users without email addresses.
  - `owner_email` optionally chooses the human group owner. When omitted, Hangar uses `ctx.user_email`.
  - `message` is optional. Toolverse posts its standard join-link message first, then this message.
  - `send_ping_msg=True` sends a final mention for email members. SeaTalk-ID members cannot be mentioned.
- `list_groups(query=None, limit=50, timeout=30)`
  - Lists groups joined by InfraBot, never groups joined by the runtime user.
  - `query` performs a case-insensitive group-name substring match.
  - `limit` defaults to 50 and must be from 1 through 100. The helper never returns an unbounded group list.
- `get_group(infrabot_group_id, timeout=30)`
  - Reads one group through InfraBot. A pre-existing group must contain InfraBot.
- `get_group_members(infrabot_group_id, timeout=30)`
  - Returns email members through InfraBot. It does not inspect the runtime user's groups or SPACE token.
- `add_group_members(infrabot_group_id, member_emails, mention_members=False, timeout=30)`
  - Requires at least one email address.
  - Adds members through InfraBot without checking runtime-user membership or `can_add_member`.
  - `mention_members=True` sends an InfraBot follow-up mentioning the added users.
- `send_group_message(infrabot_group_id=None, message, thread_id=None, timeout=30, group_id=None)`
  - Accepts the numeric InfraBot group ID, resolves the corresponding official SeaTalk group, ensures the Toolverse SOP bot is a member, and sends non-empty plain text through the SOP bot.
  - `thread_id` is optional. Pass the root SOP message ID to send a threaded reply.
  - Hangar appends `-- send by {email}` using the authenticated runtime user's email.
  - Use `infrabot_group_id`. `group_id` remains only as a deprecated compatibility alias; providing both is an error.

## Response shapes

All methods return a Toolverse response dictionary with `success`, `error_code`, and method-specific fields:

- `create_group()`: `infrabot_group_id`, compatibility alias `group_id`, `invite_link`
- `list_groups()`: `groups`, `count`; each group contains `infrabot_group_id` and `group_name`
- `get_group()`: `group` with `infrabot_group_id`, `group_name`, and available InfraBot group metadata
- `get_group_members()`: `infrabot_group_id`, `member_emails`, `count`
- `add_group_members()`: `infrabot_group_id`, `added_member_emails`, `mentioned`, optional `message_id`, and optional `mention_error` when members were added but the follow-up mention failed
- `send_group_message()`: `infrabot_group_id`, SOP `message_id`, and `thread_id`. For a root message, `thread_id` equals its new `message_id`; for a reply, `thread_id` remains the supplied root SOP message ID. Legacy Toolverse response fields are also retained.

Failures raise `seatalk.PlatformSeaTalkError`.

## Authorization

All methods require an authenticated Hangar runtime request. Hangar keeps the user's Wingman token server-side and asks for normal Toolverse integration approval when required. SeaTalk group access itself uses InfraBot's platform credential: existing-group endpoints do not read the runtime user's SPACE token, joined groups, role, or `can_add_member`.

For `create_group()`, `owner_email` is explicit when supplied and otherwise defaults to the authenticated Hangar user. For `send_group_message()`, the authenticated Hangar user is used only for the visible sender attribution appended by Hangar. App code cannot provide or spoof that sender email.

```python
from hangarkit.platform import seatalk

result = seatalk.create_group(
    group_name="Release coordination",
    owner_email="release.owner@shopee.com",
    member_emails=["jinhao.zhang@shopee.com", "jingwen.saw@shopee.com"],
    member_seatalk_ids=[9424504612],
    message="Welcome. Please use this group for release updates.",
    send_ping_msg=True,
)

infrabot_group_id = result["infrabot_group_id"]
seatalk.add_group_members(
    infrabot_group_id=infrabot_group_id,
    member_emails=["member@shopee.com"],
    mention_members=True,
)
root_message = seatalk.send_group_message(
    infrabot_group_id=infrabot_group_id,
    message="The deployment is complete.",
)
seatalk.send_group_message(
    infrabot_group_id=infrabot_group_id,
    message="Validation has also passed.",
    thread_id=root_message["thread_id"],
)
```
## Quick examples

- `result = seatalk.create_group(group_name="Release coordination", member_seatalk_ids=[9424504612], message="Welcome")`
- `groups = seatalk.list_groups(query="release", limit=20)`
- `members = seatalk.get_group_members(infrabot_group_id=123456)`
- `seatalk.add_group_members(infrabot_group_id=123456, member_emails=["member@shopee.com"], mention_members=True)`
- `seatalk.send_group_message(infrabot_group_id=123456, message="Deployment complete.")`

## Related capabilities

- `backend.hangarkit`
- `backend.integration.seatalk`
