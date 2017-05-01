#RenderMonkey
**Rendering utilities for MODO**

- dist - Distribution-ready kit and binary installers
- src - Source code
- tests - Automated testing scripts
- tools - Utilities for generating distribution files, etc.

**Branching conventions**
- `master` - Always contains the latest publicly released code. We will only use this branch after development of RM3 is complete.
- `RM3` - Always contains the latest stable RM3 code. Release-ready code _only_.
- `RM3 -> develop` - Primary development branch. This is not necessarily stable code, but should be at least usable. If you're planning to break things, use a feature branch.
- `RM3 -> develop -> feature_name` - Create feature branches while working on things that break RM. When working, merge back to develop.

*Workflow* - Check out the `develop` branch and get to work. If you plan to break something, create a feature branch from `develop`, and merge it back in when you're done. When we are ready to send a built do beta testers, we will merge `develop` into `RM3` and distribute it as a pre-release.

When we are ready to launch RM3 to the public, we will merge `RM3` into `master` and create a `develop` branch from `master`.
