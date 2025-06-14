#!/usr/bin/env python3
#
# A simple script to easily run the ai-drv-server from the CLI.
#
# In order to run this, you'll need to be in the dev shell:
#
# $nix-shell
#
# From here, you can run the server like the following.  Make sure an OpenAI API
# key is available in the environment:
#
# $ export OPENAI_API_KEY='sk-proj-vU...'
# $ ./run-server.py

import ai_drv_server.app

if __name__ == "__main__":
    ai_drv_server.app.main()
