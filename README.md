# mkAIDerivation

Automatically generate and build a Nix derivation using an LLM.

`mkAIDerivation` is as simple as:

```nix
mkAIDerivation ''
    Generate a derivation for building `xterm`
''
```

This reaches out to an LLM over the network (currently using OpenAI),
generates the `.nix` code for this derivation, imports it, and builds it.

Now you can use Nix without worrying about annoying things like
reproducibility or corretness!

## How to Use `mkAIDerivation`

This repo provides a couple different examples of using `mkAIDerivation`. You
can play around with this by first cloning this repo.

Once you have the repo, you'll need to run the `ai-drv-server` Python Flask
server.  This is used to easily proxy connections to the OpenAI API (with
[`evil-nix`](https://github.com/cdepillabout/evil-nix) being used to remove the
need for a hash).

You'll need an OpenAI API key available in the environment:

```console
$ export OPENAI_API_KEY='sk-proj-vU...'
```

And then you can run the server:

```console
$ nix run
```

Or, without Flakes:

```console
$ nix-build ./nix -A ai-drv-server
$ ./result/bin/ai-drv-server
```

Once the server is running, you can try out `mkAIDerivation`.  There is an
example in the `defaultPackage` in `flake.nix` that is setup to generate a
derivation for [`sl`](https://github.com/mtoyoda/sl) (the funny program that
animates a train in your console when you mistype `ls`).

```console
$ nix build
```

This can take quite a while to build, since it has to query the OpenAI API to
generate a derivation, and then impurely fetch it with with
[`evil-nix`](https://github.com/cdepillabout/evil-nix).

If it succeeds, you can likely run the `sl` program with from the result:

```console
$ ./result/bin/sl
```

Check out the top of `flake.nix` to play around with this and try building other
programs.

There is also a `default.nix` to use this without flakes.  Try running
`nix-build` for this.  The `default.nix` also gives you a way to pass
a prompt for the derivation on the CLI:

```console
$ nix-build --argstr msg 'Generate a derivation for building xterm'
```

## How Does `mkAIDerivation` Work?

`mkAIDerivation` mainly works by using 
[`evil-nix`](https://github.com/cdepillabout/evil-nix) to (im)purely generate
some Nix code using an LLM over the network.  And then just importing it and
building it using
[Import From Derivation (IFD)](https://nix.dev/manual/nix/2.26/language/import-from-derivation).

Here's a high-level overview of the steps:

1.  First, you need `ai-drv-server` running to help with requests to the OpenAI API.
    This could in theory be a server running on the internet.  I plan on working on
    this after getting a couple hundred million in VC money.  For now, it is just
    something you have to run locally.

    By default, `ai-drv-server` runs on `localhost:5000`.

2.  Given a call to `mkAIDerivation` like the following:

    ```nix
    mkAIDerivation "generate derivation for xterm"
    ```
    
    `mkAIDerivation` internally uses `evil-nix` to make a request to `ai-drv-server`
    like:

    ```
    GET http://localhost:5000/hash?req=generate+derivation+for+xterm
    ```

    Upon getting this request, `ai-drv-server` sends a request to OpenAI to generate
    a derivation for this prompt.  OpenAI returns something like:

    ```nix
    { lib, stdenv, fetchurl, xorg, ncurses, freetype, fontconfig, pkg-config, makeWrapper }:

    stdenv.mkDerivation rec {
      pname = "xterm";
      version = "390";
    
      src = fetchurl {
        url = "https://invisible-mirror.net/archives/xterm/${pname}-${version}.tgz";
        hash = "sha256-dRF8PMUXSgnEJe8QbmlATXL17wXgOl2gCq8VeS1vnA8=";
      };

    ...
    ```

    `ai-drv-server` caches this derivation, then hashes it, and returns just the
    hash back to `mkAIDerivation`.

    Due to the way `evil-nix` works, many of the exact same request are sent to this
    `/hash` URL in order to download all the individual bits of the resulting hash.

3.  `mkAIDerivation` uses the hash returned in the previous step to download
    the the actual raw derivation text as a
    [Fixed-Output Derivation (FOD)](https://bmcgee.ie/posts/2023/02/nix-what-are-fixed-output-derivations-and-why-use-them/).

    Imagine that the above request returned us a hash like
    `50+45s/yufGSJC5BIHYVmCsp1pAaJNBzyXYXSBUdSX8=`.

    `mkAIDerivation` now makes a FOD request to `ai-drv-server` using this hash like:

    ```nix
    fetchurl {
      url = "http://localhost:5000/drv?hash=50%2B45s/yufGSJC5BIHYVmCsp1pAaJNBzyXYXSBUdSX8%3D";
      sha256 = "sha256-50+45s/yufGSJC5BIHYVmCsp1pAaJNBzyXYXSBUdSX8=";
    }
    ```

    The `ai-drv-server` returns the raw derivation text it received from OpenAI.

4. Finally, `mkAIDerivation` internally calls `callPackage` on the above raw derivation.

5. The user crosses their fingers and hopes OpenAI didn't send them a derivation
   producing a binary that runs `rm -rf /`.

   Oh well, YOLO!

## FAQ

1.  *Should all calls to `mkDerivation` in Nixpkgs be replaced with `mkAIDerivation`?*

    Yes.

    I can't see how that would be a bad idea.

2.  *What are the downsides of using `mkAIDerivation`?*

    Your friends might think you're _too_ cool and stop hanging out with you.

    But that's okay, you can go kick it with your new friend [Tom Cruise](http://www.tomcruise.com/).

3.  *Does `mkAIDerivation` really require running `ai-drv-server`?*

    `ai-drv-server` could potentially just be some web application running on the internet.
    That would free you from having to run it locally.  (There are some obvious questions
    about authentication and API keys that would have to be answered...)

    In theory, I think it would also be possible to write `mkAIDerivation` without 
    requiring a web server for proxying requests to OpenAI.  In practice, this
    would be somewhat difficult due to how [`evil-nix`](https://github.com/cdepillabout/evil-nix)
    works.

    If someone figures this out, I'd be interested in seeing how you got it working.

4.  *How well does `mkAIDerivation` work in practice?*

    It seems to work alright for really simple things that are already in
    Nixpkgs (like the `sl` and `xterm` examples above).

    But my impression is that the popular LLMs aren't really that good at Nix
    yet. Your mileage may vary with anything more complicated.

5.  *How much engineering has gone into the system prompt sent to the OpenAI API?*

    Very little.  There is probably a bunch of low-hanging fruit here.

6.  *Does this work with other LLMs, like Claude or Gemini?*

    In theory the `ai-drv-server` could be extended to work with other popular
    LLMs, but it currently only works with OpenAI.

7.  *Could this work with local LLMs?*

    Probably?  I haven't thought much about this.