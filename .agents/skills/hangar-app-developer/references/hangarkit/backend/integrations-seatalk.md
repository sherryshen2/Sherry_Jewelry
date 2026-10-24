# SeaTalk integration

ID: `backend.integration.seatalk`
Category: `backend`

Build SeaTalk bots, verify callbacks, send messages, inspect chats, and use SeaTalk contacts/group APIs.

## Import

`from hangarkit.integrations import seatalk`

## Function inputs

Use these signatures exactly. The details below define accepted values, object shapes, side effects, and return values. Do not invent fields that are absent from a signature or documented example.

- `seatalk.configured(), verify_callback(headers, body), callback_signature_for_body(body)`
- `seatalk.listener(), listen(...), listen_webhook_event(...), read_webhook_event(...), parse_webhook_payload(...), summarize_webhook_event(...)`
- `seatalk.build_text_message(...), split_content_with_code_blocks(...), send_text_chunks_to_subscriber(...), send_text_chunks_to_group(...), send_text_chunks_to_thread(...)`
- `seatalk.send_to_group(...), send_to_subscriber(...), update_message(...), update_badge(...)`
- `seatalk.sso_verify(...), code_verify(...), get_employee_code(...), get_employee_profile(...), check_employee_existence(...)`
- `seatalk.get_bot_subscriber_list(...), get_joined_groups(...), get_all_joined_groups(...), create_group(group_owner, group_member_list, group_name="", group_settings=None), add_group_members(group_id, employee_codes), get_group_info_all_users(group_id), get_group_chat_hist(group_id, ...)`
- `seatalk.get_message_by_message_id(...), get_thread_by_thread_id(...), get_thread_by_thread_id_direct(...), download_file(...)`
- `seatalk.generate_short_url(...)`
- `seatalk.request(method, path, **kwargs)`

## Details

Use this module for SeaTalk app/bot workflows from backend code. For generic platform short links, prefer top-level `hangarkit.short_url`; `seatalk.generate_short_url()` is the SeaTalk integration-specific helper.

### Callback setup and publication

Publish the app before verifying its callback in SeaTalk—even a Private app
needs a published release. Saving, checking, or running Preview does not activate
callback code. After changing the handler, publish again to update live callbacks.
In Craft, save and check the draft, then tell the user to click Publish after the
turn finishes; do not publish mid-turn or change the app's visibility.

SeaTalk event callbacks usually arrive without a Hangar user session. Register the platform callback route `{host}{HANGAR_APP_PREFIX}/api/callback/seatalk/:slug` in SeaTalk so Hangar can acknowledge delivery before the app finishes slow bot work. Keep the app backend handler at `POST /seatalk/callback`, and keep signature verification in backend code with `seatalk.read_webhook_event(request)` or `seatalk.verify_callback(headers, body)` before processing the payload.

Use the selected app's actual host, prefix, and current slug; do not invent a
test-host URL. This platform route already accepts requests without browser
login. It does not bypass publication or provider-signature verification; a
custom public backend route is not a workaround for an unpublished app.

Hangar's SeaTalk callback gateway acknowledges non-verification deliveries immediately and forwards them to the app backend in the background. `seatalk.listener()` and `seatalk.listen_webhook_event()` likewise acknowledge non-verification callbacks immediately after signature verification and run the matched handler in the background by default. This keeps slow bot logic or LLM calls from blocking webhook delivery. If an app needs fully custom synchronous handling, call `seatalk.read_webhook_event(request)` directly and manage the response flow yourself.

### Verification and troubleshooting

For `event_type: "event_verification"`, the SDK returns JSON
`{"seatalk_challenge": "<received challenge>"}`. Do not replace it with plain text.
A generic HTTP 200 with `{"status":"accepted","async":true}` is only the
gateway's delivery acknowledgement, not proof that challenge verification or
the backend handler succeeded. Verify the actual provider response and inspect
live backend logs. First check that a release exists and includes the handler,
then check URL, event shape, signature configuration, and runtime failures.
If only a draft was saved, report that provider verification remains pending
Publish; a healthy Preview is not evidence of a working live callback.

### Group management

SeaTalk group management uses the app credentials saved under `settings.integrations.seatalk`; it is not available through user-linked integration auth. The helpers return the upstream SeaTalk response and raise `SeaTalkError` when SeaTalk returns a non-zero status code.

Create a group with an owner and at least one initial member:

```python
from hangarkit.integrations import seatalk

created = seatalk.create_group(
    group_owner=owner,
    group_member_list=initial_members,
    group_name="Incident response",
    group_settings=settings,  # optional
)
```

`group_owner` and `group_member_list` are passed through to SeaTalk unchanged, so supply the owner and member shapes required by the SeaTalk app API. HangarKit validates that both are non-empty before making the request. Omit `group_settings` when it is not needed.

Add one or more users to an existing group with SeaTalk employee codes:

```python
seatalk.add_group_members(
    group_id=created["group_id"],
    employee_codes=["employee-code-1", "employee-code-2"],
)
```

Both `group_id` and a non-empty `employee_codes` list are required. If the app starts from email addresses, call `seatalk.get_employee_code(emails)` first and use the employee codes from SeaTalk's response; do not assume a Hangar user ID is a SeaTalk employee code.
## Quick examples

- `message = seatalk.build_text_message("Hello")`
- `seatalk.send_to_group(group_id="...", message=message)`

## Related capabilities

- `backend.integrations`
