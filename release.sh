VERSION=v`python -c "import tomli; print(tomli.load(open('pyproject.toml', 'rb'))['project']['version'])"`
echo "Releasing $VERSION"
git tag $VERSION
git push origin $VERSION
