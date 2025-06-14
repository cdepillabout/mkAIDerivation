import base64
import hashlib
import json
from pprint import pprint
from typing import Any

import requests
from openai import OpenAI
from openai.types.responses.response_function_tool_call import ResponseFunctionToolCall

# TODO: This file is a bit of a mess.  There are a lot of things that should be
# cleaned up here.

# TODO: Don't create this here, but instead in `main()` and pass it down.
openai_client = OpenAI()

# The model to OpenAI model to use.
#
# gpt-4.1 is able to use the web search functionality, but 04-mini is not.
# However, o4-mini is able to use "reasoning", which could potentially give
# better results.  YMMV, I'd suggest trying both, or checking:
# https://lmarena.ai/leaderboard
#
# TODO: This should probably be a command-line argument or something.
openai_model = "gpt-4.1-2025-04-14"
# openai_model = "o4-mini-2025-04-16"


def can_model_search_web() -> bool:
    """Check if the given model supports web search preview."""
    return openai_model in {"gpt-4.1-2025-04-14"}


openai_instructions = """
    You must return a valid Nix derivation corresponding to the user's request.
    The Nix derivation must be valid and must be a derivaiton that can be passed
    to Nixpkg's top-level `callPackage` function.

    For instance, given the following user request:

    <example_user_request>
    Generate a derivation for xterm version 399
    </example_user_request>

    You must return the following Nix derivation:

    <example_response>
    {
      lib,
      stdenv,
      fetchurl,
      xorg,
      ncurses,
      freetype,
      fontconfig,
      pkg-config,
      makeWrapper,
      nixosTests,
      pkgsCross,
      gitUpdater,
      enableDecLocator ? true,
    }:

    stdenv.mkDerivation rec {
      pname = "xterm";
      version = "399";

      src = fetchurl {
        url = "https://invisible-mirror.net/archives/xterm/${pname}-${version}.tgz";
        hash = "sha256-nbNK0PU92xIj1wskfIOR5S8+SxZtathUJqTEeBPRseM=";
      };

      patches = [ ./sixel-256.support.patch ];

      strictDeps = true;

      nativeBuildInputs = [
        makeWrapper
        pkg-config
        fontconfig
      ];

      buildInputs = [
        xorg.libXaw
        xorg.xorgproto
        xorg.libXt
        xorg.libXext
        xorg.libX11
        xorg.libSM
        xorg.libICE
        ncurses
        freetype
        xorg.libXft
        xorg.luit
      ];

      configureFlags = [
        "--enable-wide-chars"
        "--enable-256-color"
        "--enable-sixel-graphics"
        "--enable-regis-graphics"
        "--enable-load-vt-fonts"
        "--enable-i18n"
        "--enable-doublechars"
        "--enable-luit"
        "--enable-mini-luit"
        "--with-tty-group=tty"
        "--with-app-defaults=$(out)/lib/X11/app-defaults"
      ] ++ lib.optional enableDecLocator "--enable-dec-locator";

      env =
        {
          # Work around broken "plink.sh".
          NIX_LDFLAGS = "-lXmu -lXt -lICE -lX11 -lfontconfig";
        }
        // lib.optionalAttrs stdenv.hostPlatform.isMusl {
          # Various symbols missing without this define: TAB3, NLDLY, CRDLY, BSDLY, FFDLY, CBAUD
          NIX_CFLAGS_COMPILE = "-D_GNU_SOURCE";
        };

      # Hack to get xterm built with the feature of releasing a possible setgid of 'utmp',
      # decided by the sysadmin to allow the xterm reporting to /var/run/utmp
      # If we used the configure option, that would have affected the xterm installation,
      # (setgid with the given group set), and at build time the environment even doesn't have
      # groups, and the builder will end up removing any setgid.
      postConfigure = ''
        echo '#define USE_UTMP_SETGID 1'
      '';

      enableParallelBuilding = true;

      postInstall = ''
        for bin in $out/bin/*; do
          wrapProgram $bin --set XAPPLRESDIR $out/lib/X11/app-defaults/
        done

        install -D -t $out/share/applications xterm.desktop
        install -D -t $out/share/icons/hicolor/48x48/apps icons/xterm-color_48x48.xpm
      '';
    }
    </example_response>

    Your response MUST be ONLY a valid Nix derivation, nothing else.
    You should never try to ask the user for any information, just
    make your best guess and return the derivation.

    Note that you SHOULD NOT include the `meta` or `passthru` attributes in
    the derivation in your response.

    The response MUST be a valid Nix expression that you can pass to `callPackage`.
    That is to say, it should start with a function call that takes a set of arguments,
    similar to the following:

    ```
    { lib, stdenv, fetchurl, ... }:
    ```

    You should not import `<nixpkgs>` anywhere within your response.

    ## How to use the Functions

    You are provided with two functions: `get_hash` and `final_derivation`.  Here is how to use them.

    ### `get_hash`

    This function can be called to get the SRI sha256 hash of a file at a given URL.

    When building Nix derivations, you will often need to download a file from a URL.
    For instance, the above xterm derivation uses the following `src` block:

    ```
    src = fetchurl {
      url = "https://invisible-mirror.net/archives/xterm/${pname}-${version}.tgz";
      hash = "sha256-nbNK0PU92xIj1wskfIOR5S8+SxZtathUJqTEeBPRseM=";
    };
    ```

    You can use the `get_hash` function to get the `hash` attribute of the
    "https://invisible-mirror.net/archives/xterm/${pname}-${version}.tgz" file.

    When you call `get_hash`, you will get the value
    `sha256-nbNK0PU92xIj1wskfIOR5S8+SxZtathUJqTEeBPRseM=` in return.  You should
    use this value for the `hash` attribute of the `fetchurl` function.

    Note that when building derivations, you will almost ALWAYS need to call
    `get_hash` exactly once for the given tarball you want to use.

    Be sure that you use `fetchurl` instead of other functions like `fetchFromGitHub`,
    Note that if you do want to download a tarball from GitHub, instead of using
    a `src` value like the following:

    ```
    src = fetchFromGitHub {
      owner = "ladislav-zezula";
      repo = "StormLib";
      rev = "v9.22";
      hash = "sha256-jFUfxLzuRHAvFE+q19i6HfGcL6GX4vKL1g7l7LOhjeU=";
    };
    ```

    You are always able to programmatically turn these into calls to `fetchurl`, like so:

    ```
    src = fetchurl {
      url = "https://github.com/ladislav-zezula/StormLib/archive/v9.22.tar.gz";
      hash = "...";
    };
    ```

    ### `final_derivation`

    This function is called to return the final derivation that you have generated.

    When you have generated final, full derivation, you MUST call this function once.
    """


# TODO: get rid of Any
openai_web_search_functions: Any = [
    {
        "type": "web_search_preview",
    },
]

# TODO: get rid of Any
openai_non_web_search_functions: Any = [
    {
        "type": "function",
        "name": "get_hash",
        "description": "Download a file from a URL and return its SRI sha256 hash as a string.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": 'The URL of the file to hash, example: "https://example.com/file.tar.gz"',
                },
            },
            "required": ["url"],
            "additionalProperties": False,
        },
        "strict": True,
    },
    {
        "type": "function",
        "name": "final_derivation",
        "description": "Return the final derivation that you have generated.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "The name of the derivation."},
                "derivation": {
                    "type": "string",
                    "description": "The final derivation that you have generated.  This should be a valid Nix expression in the form that can be passed to `callPackage`.",
                },
            },
            "required": ["name", "derivation"],
            "additionalProperties": False,
        },
        "strict": True,
    },
]


def get_hash(url: str) -> str:
    """Download the file at the given URL, compute its SRI sha256 hash, and return it as a string."""
    try:
        response = requests.get(url, stream=True, timeout=30)
        response.raise_for_status()
        sha256 = hashlib.sha256()
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                sha256.update(chunk)
        digest = sha256.digest()
        b64 = base64.b64encode(digest).decode("utf-8")
    except Exception as e:
        msg = f"Failed to fetch or hash URL {url}: {e}"
        raise RuntimeError(msg) from e

    return f"sha256-{b64}"


def query_openai_responses_api(prompt: str) -> str:
    """Query OpenAI's Responses API with the given prompt and return the response text."""
    # TODO: get rid of Any
    input_messages: Any = [
        {"role": "system", "content": openai_instructions},
        {"role": "user", "content": prompt},
    ]

    # TODO: This function is really bad.  The handling of tool calls is quite
    # hacky.

    # We have to keep looping until OpenAI calls our `final_derivation()` tool function.
    #
    # This is a bit of a hack, but it's the best way I can think of to handle
    # the fact that OpenAI's API doesn't easily support Function Calling with a final
    # Structured Output:
    # https://community.openai.com/t/how-can-i-use-function-calling-with-response-format-structured-output-feature-for-final-response/965784
    #
    # I've never seen this not work.  It seems like OpenAI is pretty good at knowning
    # it needs to call the `final_derivation()` tool function once at the end.
    # BUT WHO KNOWS WHAT WILL HAPPEN IN THE FUTURE.
    #
    # TODO: I'm sure there are various ways to work around this, including
    # reaching into the depths of the `openai` library and pulling out their
    # internal functions for parsing Structured Outputs.
    loop_count = 0

    while loop_count < 10:  # noqa: PLR2004
        loop_count += 1

        # Only some of the models allow web search.  If you try to use web search
        # with a model that doesn't support it, you will get an error from the API.
        functions = openai_non_web_search_functions + (
            openai_web_search_functions if can_model_search_web() else []
        )

        response = openai_client.responses.create(
            model=openai_model,
            input=input_messages,
            tools=functions,
            tool_choice="required",
            parallel_tool_calls=False,
        )

        pprint(f"Response: {response.model_dump()}")  # noqa: T203

        all_outputs = response.output

        for output in all_outputs:
            # Append all outputs as input messages for when we re-query the OpenAI API.
            input_messages.append(output)

        # Before trying to process the tool calls, drop all outputs we don't care about.
        response_types_to_drop = {
            # reasoning models send these reasoning outputs that we don't really care about
            "reasoning",
            # enabling web search sends these outputs that we don't really care about
            "web_search_call",
            # sometimes the model doesn't understand that we only care about the function calls
            # and tries to send messages as well.  We don't care about these.
            "message",
        }
        tool_call_outputs = [
            resp for resp in all_outputs if (resp.type not in response_types_to_drop)
        ]

        # We expect the response to contain exactly one tool call function.
        # Don't know what to do if this isn't the case.
        if len(tool_call_outputs) != 1:
            msg = f"Expected exactly one output (which should be a function call), got {len(tool_call_outputs)}: {response.model_dump()}"
            raise ValueError(msg)

        tool_call = tool_call_outputs[0]

        pprint(f"Trying to handle tool call: {tool_call.model_dump()}")  # noqa: T203

        match tool_call:
            case ResponseFunctionToolCall(name="get_hash", arguments=arguments, call_id=call_id):
                # This is a request to get the hash of a given URL.
                # Download it, get the hash, and return it to the LLM.
                args = json.loads(arguments)
                url_to_hash = args["url"]
                print(f"Hashing {url_to_hash}...")
                hsh = get_hash(url_to_hash)
                print(f"Hash for {url_to_hash} : {hsh}")
                input_messages.append(
                    {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": hsh,
                    }
                )
            case ResponseFunctionToolCall(name="final_derivation", arguments=arguments):
                # This is our final derivation.  Return it.
                args = json.loads(arguments)
                result_drv: str = args["derivation"]
                print(f"Final derivation: {result_drv}")
                return result_drv
            case _:
                msg = f"Expected ResponseFunctionToolCall with our expected tool calls, but instead got {type(tool_call)}: {response.model_dump()}"
                raise TypeError(msg)

    msg = "Failed to get a valid response from OpenAI"
    raise RuntimeError(msg)
