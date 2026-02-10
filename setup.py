import setuptools


def main() -> None:
    setuptools.setup(
        name="enapter-mcp-server",
        version=read_version(),
        description="Enapter MCP Server",
        packages=setuptools.find_packages("src"),
        package_dir={"": "src"},
        url="https://github.com/Enapter/mcp-server",
        author="Roman Novatorov",
        author_email="rnovatorov@enapter.com",
        install_requires=[
            "enapter==0.15.1",
            "fastmcp==2.14.*",
            "httpx==0.*",
        ],
    )


def read_version() -> str:
    with open("src/enapter_mcp_server/__init__.py") as f:
        local_scope: dict = {}
        exec(f.readline(), {}, local_scope)
        return local_scope["__version__"]


if __name__ == "__main__":
    main()
