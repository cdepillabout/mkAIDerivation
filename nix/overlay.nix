

final: prev: {
  mkAIDerivation = final.callPackage ./mkAIDerivation {};

  ai-drv-server = final.callPackage ../server {};
}
