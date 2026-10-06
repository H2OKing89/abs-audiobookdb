# Connect Audiobookshelf

Status: Provider workflow verified with Audiobookshelf 2.37.1  
Updated: 2026-10-05  
Owner: Quentin  
Baseline: 1.0 (runtime contract unchanged)

Install and start the adapter first. The [Unraid walkthrough](unraid.md)
explains how to do this in your browser.

## 1. Add the provider

Sign in to Audiobookshelf as an administrator. Open **Settings → Item Metadata
Utils → Custom Metadata Providers**, then click **Add**. Some versions call
the settings section **Item Metadata Tools**.

| Field | Enter |
| --- | --- |
| Name | `AudiobookDB` |
| Media Type | `Book` (already selected) |
| URL | The adapter's address; for the Unraid walkthrough, `http://YOUR_UNRAID_IP:8080`, with your server's IP substituted |
| Authorization Header Value | Your **AudiobookDB API key** |

Click **Add** to save. Use the address by itself, without `/health` or `/search`.
If you chose a different port during installation, use that port here too.

## 2. Try a book

Open a book's edit window and its **Match** tab. In the **Provider** dropdown,
choose **AudiobookDB**, enter the title and optionally the author, and click
**Search**. Check this dropdown even if you selected a default provider for
your library; the Match tab can initially select Google Books.

Select a result to review its metadata, including narrator and language.
Choose the fields you want to change, then apply the match in Audiobookshelf.
An exact Audible ASIN also works as the search text.

## Troubleshooting

| Problem | What to check |
| --- | --- |
| AudiobookDB does not appear | Confirm you saved the provider in server settings, then reopen the book's edit window. |
| Search returns nothing | Confirm the Provider dropdown says AudiobookDB and try a known title. Check the adapter logs for an error if it continues. |
| Unauthorized error in adapter logs | Check the Authorization field contains your AudiobookDB key. A plain key works. |
| Connection error | Check the adapter's health page and provider URL. For the Unraid walkthrough, use the server's LAN IP rather than `localhost`. |

The [official provider documentation](https://github.com/audiobookshelf/audiobookshelf-docs/blob/master/docs/documentation/community/community-providers.md)
describes Audiobookshelf's custom provider settings.
