
{ callPackage
, evilDownloadUrl
, fetchurl
, lib
}:

prompt:

let
  ai-drv-server-url = "http://127.0.0.1:5000";

  hash-url = "${ai-drv-server-url}/hash?req=${lib.escapeURL prompt}";

  hash-drv = evilDownloadUrl hash-url;

  hash = builtins.readFile hash-drv;

  raw-drv = fetchurl {
    url = "${ai-drv-server-url}/drv?hash=${lib.escapeURL hash}";
    sha256 = "sha256-${hash}";
  };

  drv = callPackage raw-drv {};
in

# Add the passthru.mkAIDerivation attributes to the drv
drv.overrideAttrs
  (oldAttrs:
    let
      old-passthru = oldAttrs.passthru or {};
      old-mkAIDerivation = old-passthru.mkAIDerivation or {};
    in
    {
      passthru = old-passthru // {
        mkAIDerivation = old-mkAIDerivation // {
          inherit hash prompt raw-drv;
        };
      };
    }
  )
