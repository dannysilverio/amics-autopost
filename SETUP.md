# Amics autopost setup (free)

Posts approved items from schedule.json to Instagram @amicsadagency and the linked Facebook Page.

## 1. Meta (about 20 minutes)
1. Instagram must be a Business or Creator account linked to the Amics Facebook Page.
2. developers.facebook.com > My Apps > Create App (type Business). Add Instagram Graph API and Facebook Login for Business.
3. Permissions: instagram_basic, instagram_content_publish, pages_show_list, pages_read_engagement, pages_manage_posts, business_management.
4. Graph API Explorer: generate a user token with those permissions, then exchange it for a long-lived token and fetch the Page token (never expires when derived from a long-lived user token).
5. Collect: FB_PAGE_ID, IG_USER_ID (GET /{page-id}?fields=instagram_business_account), META_TOKEN (the Page token).
6. For posting only to your own accounts, the app can stay in Development mode with you as admin. No app review needed.

## 2. GitHub
1. Create a private repo, push this folder (post.py, schedule.json, .github/workflows/post.yml).
2. Settings > Secrets and variables > Actions: add META_TOKEN, IG_USER_ID, FB_PAGE_ID.
3. Video and image URLs in schedule.json must be public. The Higgsfield CDN links work; for permanence, upload final files to a GitHub Release and use those URLs.

## 3. cron-job.org (free daily trigger)
1. Create a GitHub fine-grained token with Actions: read/write on the repo only.
2. New cron job, POST to https://api.github.com/repos/OWNER/REPO/dispatches
   Headers: Authorization: Bearer TOKEN, Accept: application/vnd.github+json
   Body: {"event_type":"post-now"}
3. Schedule it daily at the posting time. Each run posts at most one due, approved item.

## 4. Safety
- Every item starts with "approved": false. Flip it to true per item (or in batches) when ready.
- Test without posting: DRY_RUN=1 python post.py
