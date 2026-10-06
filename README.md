# abs-audiobookdb

Search [AudiobookDB](https://audiobookdb.org/) from
[Audiobookshelf](https://www.audiobookshelf.org/) and choose metadata for your
audiobooks, including covers, narrators, series, and language when available.

The adapter connects the two services. You search and review matches in
Audiobookshelf, which applies the changes you select to your library.

## What you need

- A working Audiobookshelf server and access to its administrator settings.
- Your own AudiobookDB API key.
- Unraid or another Intel/AMD 64-bit computer running Docker.
- A real contact email or public HTTPS contact URL for AudiobookDB's API requests.

## Get started

1. **Install the adapter.** Choose the guide for your setup below.
2. **Connect Audiobookshelf.** Follow the [provider setup guide](docs/audiobookshelf.md)
   to enter the adapter address and your AudiobookDB API key.
3. **Try one book.** Open its **Match** tab, select **AudiobookDB**, search,
   and review a result before applying it.

| Your setup | Start here |
| --- | --- |
| Unraid; prefer using the browser | [Unraid walkthrough](docs/unraid.md): paste a configuration into Compose Manager; no terminal commands |
| Docker Compose; comfortable with commands | [Docker setup](docs/deployment.md#docker-compose) |
| Adapter already installed | [Connect it to Audiobookshelf](docs/audiobookshelf.md) |

**Current release: v0.1.0, an early development release.** The adapter is
available as a [public container image](https://github.com/users/H2OKing89/packages/container/package/abs-audiobookdb).
Follow the walkthroughs to install it and use update buttons. The adapter is
not listed in Unraid Apps yet.

Normal installations use `:latest` for tested releases; install updates through
your Unraid or Compose Manager update button. Exact version tags remain
available for rollback.

The adapter runs on your local machine, Docker network, or private LAN.
No reverse proxy is required. Searches support title and author or an exact
Audible ASIN; exact ISBN-only lookup is not available yet.

## Help and development

Start with [Unraid troubleshooting](docs/unraid.md#troubleshooting) or
[Audiobookshelf troubleshooting](docs/audiobookshelf.md#troubleshooting).
For other problems, [open an issue](https://github.com/H2OKing89/abs-audiobookdb/issues)
with the steps you tried and any error message. Remove API keys from screenshots
and logs before sharing them.

Developers: see [CONTRIBUTING.md](CONTRIBUTING.md) for local checks.
GitHub Actions is disabled; dependency updates are tested locally before merging.
The [documentation index](docs/README.md) links configuration, design, and test records.

## License

[MIT](LICENSE) covers this project's source and documentation. AudiobookDB
API access and metadata remain subject to its own terms.
