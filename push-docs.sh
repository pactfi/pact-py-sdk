#!/bin/bash

set -e

remoteUrl=$(git remote get-url origin);
version=$(git describe --tags);

cd docs && make && cd ..

mv docs/_build/html "gh-pages/$version"

cd gh-pages

ln -sf "$version" latest

git add -A
git commit -m "Updated docs for $version"
git push origin gh-pages
