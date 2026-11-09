# Main follows the newest Minecraft version

`main` holds the newest Minecraft version Structure Lab supports, and each older version lives on a protected branch named for it, such as `26.1.2`, that takes only fixes. A port happens on a working branch and replaces `main` only once it runs: the old `main` is cut as the version branch and `main` fast-forwards to the port, so history stays linear. Structure Lab is used alongside the newest MetalForge dev client, so the newest version is where it gets run and tested.
