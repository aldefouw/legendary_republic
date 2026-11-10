# syntax=docker/dockerfile:1
ARG RUBY_VERSION=4.0.5
FROM node:22-bookworm-slim AS node
FROM ruby:${RUBY_VERSION}-slim-bookworm

ENV LANG=C.UTF-8 \
    BUNDLE_PATH=/usr/local/bundle \
    BUNDLE_FROZEN=true \
    CYPRESS_CACHE_FOLDER=/opt/cypress

# Keep Node and Ruby on the same Debian release.
COPY --from=node /usr/local/bin/node /usr/local/bin/node
COPY --from=node /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/npm
RUN ln -s ../lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s ../lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx \
    && npm install --global yarn@1.22.22

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential ca-certificates curl git pkg-config \
    imagemagick libmagickwand-dev libjpeg-dev libpng-dev libtiff-dev \
    libwebp-dev shared-mime-info default-libmysqlclient-dev default-mysql-client \
    libyaml-dev libffi-dev chromium xvfb xauth libgtk-3-0 libgbm1 \
    libnotify4 libnss3 libxss1 libasound2 libxtst6 fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
ARG BUNDLER_VERSION
COPY Gemfile Gemfile.lock ./
RUN gem install bundler --version "$BUNDLER_VERSION" --no-document \
    && bundle install --jobs 4

COPY package.json yarn.lock ./
# Yarn's postinstall downloads the matching Cypress binary outside the mount.
RUN yarn install --frozen-lockfile --non-interactive --production=false \
    && yarn cypress install \
    && yarn cypress verify \
    && yarn cache clean

COPY dependencies.sha256 /opt/ci-dependencies/dependencies.sha256
COPY entrypoint.sh /usr/local/bin/ci-entrypoint
RUN chmod +x /usr/local/bin/ci-entrypoint
ENTRYPOINT ["ci-entrypoint"]
CMD ["bash"]
