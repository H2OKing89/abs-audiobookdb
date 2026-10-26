FROM golang:1.27.3-bookworm@sha256:972b4110ba0f47539a975c31e52c64765e1ff19f2d74469ae4a595c6676e80a5 AS build
WORKDIR /src
ARG VERSION=0.1.0
ARG SOURCE_REVISION=unknown
ARG BUILD_DIRTY=unknown
COPY go.mod ./
COPY cmd ./cmd
COPY internal ./internal
RUN test "$VERSION" = "$(cat internal/buildinfo/VERSION)" && \
    CGO_ENABLED=0 go build -trimpath \
      -ldflags="-s -w -X abs-audiobookdb/internal/buildinfo.revision=$SOURCE_REVISION -X abs-audiobookdb/internal/buildinfo.dirty=$BUILD_DIRTY" \
      -o /adapter ./cmd/abs-audiobookdb

FROM scratch
ARG VERSION=0.1.0
ARG SOURCE_REVISION=unknown
LABEL org.opencontainers.image.title="abs-audiobookdb" \
      org.opencontainers.image.source="https://github.com/H2OKing89/abs-audiobookdb" \
      org.opencontainers.image.version="$VERSION" \
      org.opencontainers.image.revision="$SOURCE_REVISION" \
      org.opencontainers.image.licenses="MIT"
COPY LICENSE /licenses/adapter-MIT.txt
COPY --from=build /usr/local/go/LICENSE /licenses/Go-BSD.txt
COPY --from=build /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/ca-certificates.crt
COPY --from=build /adapter /adapter
USER 99:100
ENV GOMEMLIMIT=192MiB
EXPOSE 8080
HEALTHCHECK --interval=15s --timeout=3s --start-period=5s --retries=3 CMD ["/adapter", "health"]
ENTRYPOINT ["/adapter"]
